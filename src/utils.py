def bytes_to_gb(num_bytes: int | float) -> float:
    """
    Method which takes bytes and converts it to GB

    Args:
        num_bytes (int | float): The amount of bytes

    Returns:
        float: The bytes converted to GB
    """
    return num_bytes / 1024 / 1024 / 1024

def bytes_to_mb(num_bytes: int | float) -> float:
    """
    Method which takes bytes and converts it to MB

    Args:
        num_bytes (int | float): The amount of bytes

    Returns:
        float: The bytes converted to MB
    """
    return num_bytes / 1024 / 1024

def bytes_to_kb(num_bytes: int | float) -> float:
    """
    Method which takes bytes and converts it to KB

    Args:
        num_bytes (int | float): The amount of bytes

    Returns:
        float: The bytes converted to KB
    """
    return num_bytes / 1024

def format_bytes(num_bytes: int | float) -> str:
    """
    Method which takes bytes and decides if to convert it to MB or GB

    Args:
        num_bytes (int | float): The amount of bytes

    Returns:
        str: The bytes converted to either MB or GB as a string
    """
    if num_bytes > 1024 * 1024 * 1024:
        return f"{bytes_to_gb(num_bytes):.2f} GB"
    return f"{bytes_to_mb(num_bytes):.2f} MB"

def format_speed(bytes_per_sec: float) -> str:
    """
    Takes bytes per second and formats it to the most readable unit

    Args:
        bytes_per_sec (float): Speed in bytes per second

    Returns:
        str: The speed formatted as Kbps, Mbps or Gbps
    """
    if bytes_per_sec >= 1024 * 1024 * 1024:
        return f"{bytes_to_gb(bytes_per_sec) * 8:.2f} Gbps"
    if bytes_per_sec >= 1024 * 1024:
        return f"{bytes_to_mb(bytes_per_sec) * 8:.2f} Mbps"
    return f"{bytes_to_kb(bytes_per_sec) * 8:.2f} Kbps"

def get_color(percent: float) -> str:
    """
    Takes a percentage input and converts it to a rich color name

    Args:
        percent (float): Percent used / full

    Returns:
        str: A rich color name based on the percentage
    """
    if percent >= 90.0:
        return "red"
    if percent >= 75.0:
        return "orange1"
    if percent >= 60.0:
        return "yellow"
    return "green"
