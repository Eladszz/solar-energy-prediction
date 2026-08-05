import {
  CircleDollarSign,
  CloudSun,
  GitCompareArrows,
  Info,
  LayoutDashboard,
} from 'lucide-react';
import type {ReactNode} from 'react';

import {Tabs, TabsContent, TabsList, TabsTrigger} from '@/components/ui/tabs';
import type {Copy, SectionId} from '@/src/i18n';

const DASHBOARD_TABS: Array<{id: SectionId; label: keyof Copy; icon: typeof LayoutDashboard}> = [
  {id: 'overview', label: 'overview', icon: LayoutDashboard},
  {id: 'forecast', label: 'forecast', icon: CloudSun},
  {id: 'scenarios', label: 'scenarios', icon: GitCompareArrows},
  {id: 'finance', label: 'finance', icon: CircleDollarSign},
  {id: 'methodology', label: 'methodology', icon: Info},
];

export function DashboardTabs({copy, activeSection, onChange, children}: {
  copy: Copy;
  activeSection: SectionId;
  onChange: (section: SectionId) => void;
  children: ReactNode;
}) {
  return <Tabs value={activeSection} onValueChange={(value) => onChange(value as SectionId)} className="gap-0">
    <div className="mb-5 overflow-x-auto rounded-2xl border bg-card/80 px-2 shadow-sm backdrop-blur">
      <TabsList variant="line" aria-label={copy.navigation} className="h-auto min-w-max justify-start gap-1 py-2">
        {DASHBOARD_TABS.map(({id, label, icon: Icon}) => <TabsTrigger key={id} value={id} className="h-11 flex-none rounded-xl px-4 text-sm font-bold data-active:bg-sky-50 data-active:text-sky-700 dark:data-active:bg-sky-950/40 dark:data-active:text-sky-300">
          <Icon />{copy[label]}
        </TabsTrigger>)}
      </TabsList>
    </div>
    <TabsContent value={activeSection}>{children}</TabsContent>
  </Tabs>;
}
