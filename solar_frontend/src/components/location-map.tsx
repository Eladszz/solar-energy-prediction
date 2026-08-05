import {useEffect, useRef, type MutableRefObject} from 'react';
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import {MapPin, Pentagon, Search, SquareDashed} from 'lucide-react';
import {FeatureGroup, MapContainer, Marker, TileLayer, useMap, useMapEvents} from 'react-leaflet';
import {EditControl} from 'react-leaflet-draw';

import {Button} from '@/components/ui/button';
import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card';
import {Input} from '@/components/ui/input';
import {Label} from '@/components/ui/label';
import {formatNumber} from '@/src/formatters';
import type {Copy, Language} from '@/src/i18n';

declare global {
  interface Window { type?: string }
}

// leaflet-draw 1.0.4 assigns to a legacy global while formatting live area tooltips.
// Defining the binding keeps rectangle and polygon drawing compatible in ES modules.
if (typeof window !== 'undefined' && window.type === undefined) window.type = '';

L.Marker.prototype.options.icon = L.icon({iconUrl: icon, shadowUrl: iconShadow, iconSize: [25, 41], iconAnchor: [12, 41]});

export type Position = {lat: number; lng: number};

interface LocationMapProps {
  language: Language;
  copy: Copy;
  position: Position;
  onPositionChange: (position: Position) => void;
  panelArea: number;
  onPanelAreaChange: (area: number) => void;
  searchQuery: string;
  onSearchQueryChange: (query: string) => void;
  onSearch: () => void;
  searching: boolean;
}

function MapViewport({position}: {position: Position}) {
  const map = useMap();
  useEffect(() => { map.flyTo(position, map.getZoom(), {animate: true, duration: 0.6}); }, [map, position]);
  return null;
}

function MapClick({isDrawing, onClick}: {isDrawing: MutableRefObject<boolean>; onClick: (position: Position) => void}) {
  useMapEvents({click: (event) => { if (!isDrawing.current) onClick(event.latlng); }});
  return null;
}

function polygonAreaM2(layer: L.Polygon): number {
  const latLngs = layer.getLatLngs();
  const first = latLngs[0];
  const ring = first instanceof L.LatLng ? latLngs as L.LatLng[] : Array.isArray(first) ? first as L.LatLng[] : [];
  if (ring.length < 3) return 0;

  const earthRadiusM = 6_378_137;
  const referenceLatitude = ring.reduce((sum, point) => sum + point.lat, 0) / ring.length * Math.PI / 180;
  const projected = ring.map((point) => ({
    x: earthRadiusM * point.lng * Math.PI / 180 * Math.cos(referenceLatitude),
    y: earthRadiusM * point.lat * Math.PI / 180,
  }));
  const doubleArea = projected.reduce((sum, point, index) => {
    const next = projected[(index + 1) % projected.length];
    return sum + point.x * next.y - next.x * point.y;
  }, 0);
  return Math.abs(doubleArea) / 2;
}

function selectedAreaM2(layer: L.Layer): number {
  return layer instanceof L.Polygon ? polygonAreaM2(layer) : 0;
}

function layerCenter(layer: L.Layer): Position | null {
  if (!(layer instanceof L.Polygon)) return null;
  const center = layer.getBounds().getCenter();
  return {lat: center.lat, lng: center.lng};
}

function localizeDrawingControls(copy: Copy) {
  L.drawLocal.draw.toolbar.buttons.rectangle = copy.drawRectangle;
  L.drawLocal.draw.toolbar.buttons.polygon = copy.drawPolygon;
  L.drawLocal.draw.toolbar.actions.title = copy.cancelDrawing;
  L.drawLocal.draw.toolbar.actions.text = copy.cancelDrawing;
  L.drawLocal.draw.toolbar.finish.title = copy.finishDrawing;
  L.drawLocal.draw.toolbar.finish.text = copy.finishDrawing;
  L.drawLocal.draw.toolbar.undo.title = copy.undoPoint;
  L.drawLocal.draw.toolbar.undo.text = copy.undoPoint;
  L.drawLocal.draw.handlers.rectangle.tooltip.start = copy.rectangleStart;
  L.drawLocal.draw.handlers.polygon.tooltip.start = copy.polygonStart;
  L.drawLocal.draw.handlers.polygon.tooltip.cont = copy.polygonContinue;
  L.drawLocal.draw.handlers.polygon.tooltip.end = copy.polygonFinish;
  L.drawLocal.edit.toolbar.buttons.edit = copy.editShape;
  L.drawLocal.edit.toolbar.buttons.remove = copy.deleteShape;
  L.drawLocal.edit.toolbar.actions.save.title = copy.saveChanges;
  L.drawLocal.edit.toolbar.actions.save.text = copy.saveChanges;
  L.drawLocal.edit.toolbar.actions.cancel.title = copy.cancelDrawing;
  L.drawLocal.edit.toolbar.actions.cancel.text = copy.cancelDrawing;
  L.drawLocal.edit.toolbar.actions.clearAll.title = copy.clearShapes;
  L.drawLocal.edit.toolbar.actions.clearAll.text = copy.clearShapes;
  L.drawLocal.edit.handlers.edit.tooltip.text = copy.shapeEditHelp;
  L.drawLocal.edit.handlers.remove.tooltip.text = copy.shapeDeleteHelp;
}

export function LocationMap(props: LocationMapProps) {
  const featureGroupRef = useRef<L.FeatureGroup | null>(null);
  const isDrawingRef = useRef(false);

  localizeDrawingControls(props.copy);

  const clearShapes = () => featureGroupRef.current?.clearLayers();
  const applyLayer = (layer: L.Layer) => {
    const area = selectedAreaM2(layer);
    const center = layerCenter(layer);
    if (area > 0) props.onPanelAreaChange(Number(area.toFixed(2)));
    if (center) props.onPositionChange(center);
  };

  const handleCreated = (event: L.DrawEvents.Created) => {
    featureGroupRef.current?.eachLayer((layer) => {
      if (layer !== event.layer) featureGroupRef.current?.removeLayer(layer);
    });
    applyLayer(event.layer);
  };

  const handleEdited = (event: L.DrawEvents.Edited) => {
    event.layers.eachLayer((layer) => applyLayer(layer));
  };

  const handleSearch = () => {
    clearShapes();
    props.onSearch();
  };

  const handleMapClick = (position: Position) => {
    clearShapes();
    props.onPositionChange(position);
  };

  return <Card className="mb-6 overflow-hidden border-border/70 shadow-sm">
    <CardHeader className="gap-4 border-b bg-card/80 lg:flex-row lg:items-end lg:justify-between">
      <div className="space-y-1.5">
        <CardTitle className="flex items-center gap-2 text-xl"><MapPin className="size-5 text-sky-600" />{props.copy.locationTitle}</CardTitle>
        <p className="max-w-3xl text-sm leading-6 text-muted-foreground">{props.copy.locationIntro}</p>
      </div>
      <div className="w-full space-y-1.5 lg:max-w-xl">
        <Label>{props.copy.address}</Label>
        <div className="flex gap-2">
          <Input value={props.searchQuery} onChange={(event) => props.onSearchQueryChange(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && handleSearch()} placeholder={props.copy.addressPlaceholder} />
          <Button variant="secondary" onClick={handleSearch} disabled={props.searching}>{props.searching ? props.copy.searching : <><Search />{props.copy.find}</>}</Button>
        </div>
      </div>
    </CardHeader>
    <CardContent className="p-0">
      <div className="relative z-0 h-[360px] sm:h-[420px]" data-testid="location-selection-map">
        <MapContainer center={props.position} zoom={18} className="h-full w-full" scrollWheelZoom>
          <MapViewport position={props.position} />
          <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <FeatureGroup ref={featureGroupRef}>
            <EditControl
              key={props.language}
              position={props.language === 'he' ? 'topleft' : 'topright'}
              onCreated={handleCreated}
              onEdited={handleEdited}
              onDrawStart={() => { isDrawingRef.current = true; }}
              onDrawStop={() => { window.setTimeout(() => { isDrawingRef.current = false; }, 100); }}
              draw={{rectangle: true, polygon: true, circle: false, circlemarker: false, marker: false, polyline: false}}
            />
          </FeatureGroup>
          <Marker position={props.position} />
          <MapClick isDrawing={isDrawingRef} onClick={handleMapClick} />
        </MapContainer>
      </div>
      <div className="grid gap-3 border-t bg-muted/25 p-4 sm:grid-cols-3">
        <div className="rounded-xl bg-background px-3 py-2"><p className="text-xs font-bold text-muted-foreground">{props.copy.coordinates}</p><p dir="ltr" className="mt-1 font-mono text-sm font-semibold">{props.position.lat.toFixed(5)}, {props.position.lng.toFixed(5)}</p></div>
        <div className="rounded-xl bg-background px-3 py-2"><p className="text-xs font-bold text-muted-foreground">{props.copy.selectedArea}</p><p dir="auto" className="mt-1 text-sm font-semibold">{formatNumber(props.panelArea, props.language, 2)} m²</p></div>
        <div className="rounded-xl bg-background px-3 py-2"><p className="flex items-center gap-1.5 text-xs font-bold text-muted-foreground"><SquareDashed className="size-3.5" /><Pentagon className="size-3.5" />{props.copy.drawingTools}</p><p className="mt-1 text-xs leading-5 text-muted-foreground">{props.copy.mapHint}</p></div>
      </div>
    </CardContent>
  </Card>;
}
