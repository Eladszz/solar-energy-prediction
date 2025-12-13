def get_cleanliness_loss(level: str) -> float:
    # Return fractional loss
    levels = {
        "clean": 0.02,
        "normal": 0.05,
        "dusty": 0.10
    }
    return levels.get(level, 0.05)


def get_shading_loss(level: str) -> float:
    levels = {
        "none": 0.00,
        "low": 0.03,
        "medium": 0.07,
        "high": 0.15
    }
    return levels.get(level, 0.03)


def compute_system_loss_factor(cleanliness: str, shading: str) -> float:
    """
    Compute aggregated system loss factor.
    Example:
        - cleanliness loss: 5%
        - shading loss: 3%
        - wiring loss: 2%
        - inverter efficiency: 96%
    """

    cleanliness_loss = get_cleanliness_loss(cleanliness)
    shading_loss = get_shading_loss(shading)
    wiring_loss = 0.02
    inverter_efficiency = 0.96   # 96%

    system_factor = (
        (1 - cleanliness_loss) *
        (1 - shading_loss) *
        (1 - wiring_loss) *
        inverter_efficiency
    )

    return system_factor
