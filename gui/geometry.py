from math import sin, cos, radians, degrees, atan
from typing import Tuple, List, Union, Optional

# Geometry functions #################################################

def getSineCosine(theta: int) -> Tuple[float]:
    '''
    Return sine of cosine of an angle in degrees
    '''
    # Avoid floating point problems when sin or cos should be 0.
    if theta % 180 == 0:
        s = 0
        c = cos(radians(theta))
    elif theta % 90 == 0:
        s = sin(radians(theta))
        c = 0
    else:
        s = sin(radians(theta))
        c = cos(radians(theta))
    return s, c

def flatToTupleCoords(coords: Union[list, tuple]) -> List[tuple]:
    '''
    Converts a flat list of coordinates into a list of tuples
    '''
    if not all(isinstance(x, tuple) for x in coords):
        coords = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
    return coords

def getCenterCoord(coords: Union[list, tuple]) -> tuple:
    '''
    Calculates the center coordinate of a polygon via a simple average of vertices
    '''
    flat_coords = flatToTupleCoords(coords)
    avg_x = sum([x[0] for x in flat_coords]) / len(flat_coords)
    avg_y = sum([x[1] for x in flat_coords]) / len(flat_coords)
    return (avg_x, avg_y)

def rotatePolygon(coords: Union[list, tuple], theta: int, pivot_point: Optional[tuple]=None) -> Union[list, tuple]:
    '''
    Rotate each vertice of a polygon an angle = theta (in degrees)
    Coords can be a list of tuples [(x, y), ...] or a flat list [x1, y1, x2, y2 ...]
    If pivot_point is not provided, a simple average is calculated and used
    '''
    # If coords is a flat list of numbers (generated by Tkinter's coords method, for example), convert to list of tuples
    flatten_output = False
    if not all(isinstance(x, tuple) for x in coords):
        coords = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
        flatten_output = True

    # Calculate pivot point if needed
    if not pivot_point:
        pivot_point = getCenterCoord(coords)
    
    # Get sine and cosine of rotation angle
    sine, cosine = getSineCosine(theta)

    # Rotate each vertex
    newcoords = []
    for coord in coords:
        # Transpose pivot point to origin
        origin_x = coord[0] - pivot_point[0]
        origin_y = coord[1] - pivot_point[1]
        
        # Rotate
        new_x = origin_x*cosine - origin_y*sine
        new_y = origin_x*sine + origin_y*cosine
        
        # Transpose back from origin
        new_x += pivot_point[0]
        new_y += pivot_point[1]
        
        # If input was a flattened list, return a flattened list
        if flatten_output:
            newcoords.extend((new_x, new_y))
        else:
            newcoords.append((new_x, new_y))

    return newcoords

def getInclination(origin: tuple, tip: tuple, vertical_reference: bool=True) -> float: 
    '''
    Get inclination in degrees of a line. Returns always a positive angle less than 360
    '''
    try:
        slope = getSlope(origin, tip, absolute=False)
        inclination = degrees(atan(slope))
    except ZeroDivisionError: #Vertical line - undefined slope
        if tip[1] > origin[1]:
            inclination = 90.0
        else:
            inclination = 270.0
    
    # Correct for tip being present in left quadrants
    if tip[0] < origin[0]:
        inclination += 180
    
    # Offset calculation so that a vertical line is considered having a 0 degrees inclinations
    if vertical_reference:
        inclination -= 270.0 
    
    # Convert to an angle within 360 degrees
    inclination %= 360
    
    return inclination

def getSlope(origin: tuple, tip: tuple, absolute: bool=True) -> float:
    '''
    Get slope of the inclination of a line.
    If absolute is True, return always a positive slope.
    '''
    x1, y1 = origin[0], origin[1]
    x2, y2 = tip[0], tip[1]
    slope = (y2-y1) / (x2-x1)
    if absolute:
        return abs(slope)
    else:
        return slope

#######################################################################