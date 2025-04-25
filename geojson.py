import uuid, json
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Iterator, Any


class Jsonable(ABC):
    @classmethod
    @abstractmethod
    def to_json(cls) -> dict[str, Any]:
        """
        Converts the object to a JSON object

        Returns:
            object: The object as a JSON object
        """

    def __str__(self) -> str:
        return str(self.to_json())

class GeoJSONException(Exception):
    """
    Represents a GeoJSON exception
    """
    def __init__(self, message: str) -> None:
        self.message = message
        super(Exception, self).__init__(message)

class FeatureException(GeoJSONException):
    """
    Represents a Feature exception
    """
    def __init__(self, message: str) -> None:
        self.message = message
        super(Exception, self).__init__(message)

class FeatureType:
    """
    Represents all feature types supported by GeoJSON
    """
    POINT = "Point"
    MULTI_POINT = "MultiPoint"
    LINE_STRING = "LineString"
    MULTI_LINE_STRING = "MultiLineString"
    POLYGON = "Polygon"
    MULTI_POLYGON = "MultiPolygon"
    GEOMETRY_COLLECTION = "GeometryCollection"

@dataclass
class Layer(Jsonable):
    """
    A set of methods from the Layer base class that all Leaflet layers use.
    """
    pane: str = None
    attribution: str = None

    def to_json(self) -> dict[str, Any]:
        return add_not_empty(
            {},
            "options",
            compact_options(
                pane=self.pane,
                attribution=self.attribution
            )
        )

@dataclass
class InteractiveLayer(Layer):
    """
    Some Layers can be made interactive - when the user interacts with such a layer,
    mouse events like click and mouseover can be handled.
    """
    interactive: bool = None
    bubbling_mouse_events: bool = None

    def to_json(self):
        return soft_update(
            super().to_json(),
            add_not_empty(
                {},
                "options",
                compact_options(
                    interactive=self.interactive,
                    bubbling_mouse_events=self.bubbling_mouse_events
                )
            )
        )

@dataclass
class DivOverlay(InteractiveLayer):
    """
    Base model for Popup and Tooltip.
    """
    interactive: bool = None
    offset: tuple = None
    class_name: str = None
    pane: str = None
    content: str|object = None

    def to_json(self):
        return soft_update(
            super().to_json(),
            add_not_empty(
                { "content": self.content },
                "options",
                compact_options(
                    interactive=self.interactive,
                    offset={ "x": self.offset[0], "y": self.offset[1] } if self.offset else None,
                    className=self.class_name,
                    pane=self.pane,
                )
            )
        )

@dataclass
class Icon(Jsonable):
    path: str = ""
    size: list = field(default_factory=lambda: [100, 100])
    color: str = "black"

    def to_json(self):
        return {
            "path": self.path,
            "size": {
                "width": self.size[0],
                "height": self.size[1]
            },
            "color": self.color
        }

@dataclass
class Tooltip(DivOverlay):
    text: str = ""
    offset: tuple = None
    direction: str = None
    permanent: bool = None
    sticky: bool = None
    opacity: float = None

    def __post_init__(self):
        self.content = {
            "text": self.text
        }

    def to_json(self):
        return soft_update(
            super().to_json(),
            add_not_empty(
                {},
                "options",
                compact_options(
                    offset={ "x": self.offset[0], "y": self.offset[1] } if self.offset else None,
                    direction=self.direction,
                    permanent=self.permanent,
                    sticky=self.sticky,
                    opacity=self.opacity,
                )
            )
        )

@dataclass
class Popup(DivOverlay):
    text: str = ""
    pane: str = None
    offset: tuple = None
    maxWidth: int = None
    minWidth: int = None
    maxHeight: int = None
    autoPan: bool = None
    autoPanPaddingTopLeft: tuple = None
    autoPanPaddingBottomRight: tuple = None
    autoPanPadding: tuple = None
    keepInView: bool = None
    closeButton: bool = None
    autoClose: bool = None
    closeOnEscapeKey: bool = None
    closeOnClick: bool = None
    className: bool = None

    def __post_init__(self):
        self.content = {
            "text": self.text
        }

    def to_json(self):
        return soft_update(
            super().to_json(),
            add_not_empty(
                {},
                "options",
                compact_options(
                    pane=self.pane,
                    offset={ "x": self.offset[0], "y": self.offset[1] } if self.offset else None,
                    maxWidth=self.maxWidth,
                    minWidth=self.minWidth,
                    maxHeight=self.maxHeight,
                    autoPan=self.autoPan,
                    autoPanPaddingTopLeft=self.autoPanPaddingTopLeft,
                    autoPanPaddingBottomRight=self.autoPanPaddingBottomRight,
                    autoPanPadding=self.autoPanPadding,
                    keepInView=self.keepInView,
                    closeButton=self.closeButton,
                    autoClose=self.autoClose,
                    closeOnEscapeKey=self.closeOnEscapeKey,
                    closeOnClick=self.closeOnClick,
                    className=self.className
                )
            )
        )

@dataclass
class Marker(Jsonable):
    """
    Used to display clickable/draggable icons on the map.
    """
    icon: Icon = None
    tooltip: Tooltip = None
    popup: Popup = None

    def to_json(self):
        return soft_updates(
            add_not_empty({}, "icon", self.icon.to_json()) if self.icon else {},
            add_not_empty({}, "tooltip", self.tooltip.to_json()) if self.tooltip else {},
            add_not_empty({}, "popup", self.popup.to_json()) if self.popup else {}
        )

class Feature(Jsonable):

    def __init__(self, obj=None, f_type=""):
        self.feature_type = f_type
        self.required_keys = ["type", "properties", "geometry"]
        self.id = uuid.uuid4().hex
        self.properties = {}
        self.marker = None
        self.marker = None
        self.geometry = {
            "type": f_type,
            "coordinates": []
        }

        if obj is not None:
            self.load_json_object(obj)

    def load_json_object(self, obj):
        """

        Args:
            obj:

        Returns:

        """
        if "type" not in obj or obj["type"] != "Feature":
            raise KeyError("Missing or invalid required key \"type\"!\n" + str(obj.to_json()))

        missing_keys = [key for key in self.required_keys if key not in obj]
        if missing_keys:
            raise FeatureException("Missing or invalid required key(s) %s!" % missing_keys)

        self.properties = obj["properties"]
        self.geometry = obj["geometry"]

    def to_json(self):
        obj = {
            "type": "Feature",
            "id": self.id,
            "properties": self.properties,
            "geometry": self.geometry,
        }

        if self.marker is not None:
            obj["marker"] = self.marker.to_json()
        return obj

    def __str__(self):
        return json.dumps(self.to_json())

    @classmethod
    @abstractmethod
    def create(cls):
        """
        Creates a new Feature object

        Returns:
            Feature: The Feature object
        """

    @classmethod
    def create(cls):
        return Feature(None)

    @classmethod
    @abstractmethod
    def many(cls):
        """
        Creates any number of Feature objects

        Returns:
            List[Feature]: The list of Feature objects
        """

    @classmethod
    def many(cls, num):
        return [Feature(None) for _ in range(num)]

class MultiFeature(Feature):

    def __init__(self, _type, obj=None):
        super().__init__(obj, _type)
        self._type = _type
        self.features = []

    def load_json_object(self, obj):
        return super().load_json_object(obj)

    def to_json(self):
        return super().to_json()

    def __str__(self):
        return super().__str__()

    @classmethod
    @abstractmethod
    def create(cls):
        """
        Creates a new MultiFeature object

        Returns:
            MultiFeature: The MultiFeature object
        """

    @classmethod
    @abstractmethod
    def many(cls):
        """
        Creates any number of MultiFeature objects

        Returns:
            List[MultiFeature]: The list of MultiFeature objects
        """

    def add(self, obj):
        """
        Adds a feature to the MultiFeature object

        Args:
            obj: The feature to add to the MultiFeature object
        """
        if not isinstance(obj, self._type):
            raise TypeError("Expected a %s object!" % type(self._type).__name__)
        self.features.append(obj)

    def remove(self, obj):
        """
        Removes a feature from the MultiFeature object

        Args:
            obj: The feature to remove from the MultiFeature object
        """
        if not isinstance(obj, self._type):
            raise TypeError("Expected a %s object!" % type(self._type).__name__)
        self.features.remove(obj)

class Point(Feature):
    def __init__(self, obj=None):
        super().__init__(obj, FeatureType.POINT)

        if obj is not None:
            self.create(*obj["geometry"]["coordinates"])

    @classmethod
    def create(cls, x, y):
        obj = cls()
        obj.geometry["coordinates"].append(x)
        obj.geometry["coordinates"].append(y)
        return obj

    @classmethod
    def many(cls, *positions):
        points = []
        for pos in positions:
            points.append(Point.create(*pos))
        return points

class MultiPoint(MultiFeature):
    def __init__(self, obj=None):
        super().__init__(FeatureType.MULTI_POINT, obj)

    @classmethod
    def create(cls, *points):
        obj = cls()
        for point in points:
            if not isinstance(point, Point):
                raise FeatureException("Feature must be of type Point!")
            obj.geometry["coordinates"].append(point.geometry["coordinates"])
        return obj

    @classmethod
    def many(cls, *multi_points):
        obj = []
        for multi_point in multi_points:
            points = []
            for point in multi_point:
                points.append(Point.create(*point))
            obj.append(MultiPoint.create(*points))
        return obj

class LineString(Feature):
    def __init__(self, obj=None):
        super().__init__(obj, FeatureType.LINE_STRING)

    @classmethod
    def create(cls, *points):
        obj = cls()
        for point in points:
            if not isinstance(point, Point):
                raise FeatureException("Feature must be of type LineString!")
            obj.geometry["coordinates"].append(point.geometry["coordinates"])
        return obj

    @classmethod
    def many(cls, *line_strings):
        obj = []
        for line_string in line_strings:
            points = []
            for point in line_string:
                points.append(Point.create(point[0], point[1]))
            obj.append(LineString.create(*points))
        return obj

class MultiLineString(MultiFeature):
    def __init__(self, obj=None):
        super().__init__(FeatureType.MULTI_LINE_STRING, obj)

    @classmethod
    def create(cls, *line_strings):
        obj = cls()
        for line_string in line_strings:
            if not isinstance(line_string, LineString):
                raise FeatureException("Feature must be of type LineString!")
            obj.geometry["coordinates"].append(line_string.geometry["coordinates"])
        return obj

    @classmethod
    def many(cls, *multi_line_strings):
        obj = []
        for multi_line_string in multi_line_strings:
            line_strings = []
            for line_string in multi_line_string:
                points = []
                for point in line_string:
                    points.append(Point.create(*point))
                line_strings.append(LineString.create(*points))
            obj.append(MultiLineString.create(*line_strings))
        return obj

class Polygon(Feature):
    def __init__(self, obj=None):
        super().__init__(obj, FeatureType.POLYGON)

    @classmethod
    def create(cls, *points):
        obj = cls()
        obj.geometry["coordinates"].append([])
        for point in points:
            if not isinstance(point, Point):
                raise FeatureException("Feature must be of type Point!")
            obj.geometry["coordinates"][0].append(point.geometry["coordinates"])
        return obj

    @classmethod
    def many(cls, *polygons):
        obj = []
        for polygon in polygons:
            points = []
            for point in polygon:
                points.append(Point.create(*point))
            obj.append(Polygon.create(*points))
        return obj

class MultiPolygon(MultiFeature):
    def __init__(self, obj=None):
        super().__init__(FeatureType.MULTI_POLYGON, obj)

    @classmethod
    def create(cls, *polygons):
        obj = cls()
        for polygon in polygons:
            if not isinstance(polygon, Polygon):
                raise FeatureException("Feature must be of type Polygon!")
            obj.geometry["coordinates"].append(polygon.geometry["coordinates"])
        return obj

    @classmethod
    def many(cls, *multi_polygons):
        obj = []
        for multi_polygon in multi_polygons:
            polygons = []
            for polygon in multi_polygon:
                points = []
                for point in polygon:
                    points.append(Point.create(*point))
                polygons.append(Polygon.create(*points))
            obj.append(MultiPolygon.create(*polygons))
        return obj

class GeometryCollection(MultiFeature):
    def __init__(self, obj=None):
        self.geometries = []
        super().__init__(FeatureType.GEOMETRY_COLLECTION, obj)

    @classmethod
    def create(cls, *features):
        obj = cls()
        for feature in features:
            if isinstance(feature, Feature):
                obj.geometries.append(feature)
                continue

            obj.geometries.append(convert_feature(feature))
        return obj

    @classmethod
    def many(cls, *geometry_collections):
        obj = []
        for geometry_collection in geometry_collections:
            features = []
            for feature in geometry_collection:
                features.append(feature)
            obj.append(GeometryCollection.create(*features))
        return obj

    def add(self, obj):
        """
        Adds a feature to the GeometryCollection object

        Args:
            obj: The feature to add to the GeometryCollection object
        """
        if not isinstance(obj, Feature):
            raise TypeError("Expected a Feature object!")
        self.geometries.append(obj)

    def remove(self, obj):
        """
        Removes a feature from the GeometryCollection object

        Args:
            obj: The feature to remove from the GeometryCollection object
        """
        if not isinstance(obj, Feature):
            raise TypeError("Expected a Feature object!")
        self.geometries.remove(obj)

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
        return {
            "type": "Feature",
            "id": self.id,
            "properties": self.properties,
            "geometry": {
                "type": "GeometryCollection",
                "geometries": [{ "type": feature.feature_type, "coordinates": feature.geometry["coordinates"] } for feature in self.geometries]
            }
        }

class GeoJSON(Jsonable):
    """
    Objective representation of a GeoJSON object

    Follows the GeoJSON RFC 7946 specification (https://geojson.org/)

    Added UI functionality implemented by the following documentation and references:
     + LeafletJS(https://leafletjs.com/reference.html)
     + Ignition (https://www.docs.inductiveautomation.com/docs/8.1/appendix/components/perspective-components/perspective-display-palette/perspective-map)
    """
    def __init__(self, obj: dict = None) -> None:
        self.type = "FeatureCollection"
        self.features = []
        self.aliases = {}

        if obj is not None:
            self.load_json_object(obj)

    def __str__(self) -> str:
        """
        Returns a string representation of the object's GeoJSON.

        Returns:
            str: A string representation of the object's GeoJSON.
        """
        return json.dumps(self.to_json())

    def __getitem__(self, key) -> Feature | None:
        """
        Indexes the GeoJSON object with a given ID

        Args:
            key: The index of the feature to get

        Returns:
            Feature | None: The feature at the specified index in [self.features], None if it does not exist
        """
        try:
            return self.features[key]
        except IndexError:
            return None

    def __iter__(self) -> Iterator[Feature]:
        """
        Provides an iterator over the features GeoJSON object

        Returns:
            Iterator: An iterator over the GeoJSON object
        """
        return self.features.__iter__()

    def __len__(self) -> int:
        """
        Returns the number of features in the GeoJSON object

        Returns:
            int: The number of features in the GeoJSON object
        """
        return self.features.__len__()

    def __contains__(self, item: Feature) -> bool:
        """
        Returns whether the GeoJSON object contains a given feature

        Args:
            item: The Feature object to check for

        Returns:
            bool: Whether the GeoJSON object contains the given feature
        """
        if not isinstance(item, FeatureType):
            raise TypeError("Expected a Feature object!")
        return item in self.features

    def add_feature(self, feature: Feature, alias: str = None) -> None:
        self.features.append(feature)
        if alias is not None:
            self.aliases[alias] = feature.id

    def remove_feature(self, feature: Feature) -> None:
        """
        Removes a feature from the GeoJSON object

        Args:
            feature: The feature to remove from the GeoJSON object
        """
        if not isinstance(feature, Feature):
            raise TypeError("Expected a Feature object!")
        self.features.remove(feature)
        for alias, id in self.aliases.items():
            if id == feature.id:
                del self.aliases[alias]
                break

    def count(self, _type: FeatureType) -> int:
        """
        Counts the number of features in the GeoJSON object of type _type

        Args:
            _type: The type of feature to count

        Returns:
            int: The number of features in the GeoJSON object of type _type
        """
        if not isinstance(_type, FeatureType):
            raise TypeError("Type must be of type FeatureType!")

        return len([f for f in self.features if f.feature_type == _type])

    def at_id(self, _id: str) -> Feature | None:
        """
        Retrieves a feature by its id

        Args:
            _id: The id of the feature to retrieve

        Returns:
            Feature | None: The feature with the specified id, None if the id does not exist
        """
        res = [f for f in self.features if f.id == id][0]
        return res if res else None

    def at_alias(self, alias: str) -> Feature | None:
        """
        Retrieves a feature by the specified alias

        Args:
            alias: The alias of a feature to find

        Returns:
            Feature | None: The feature with the specified alias, None if the alias does not exist
        """
        _id = self.aliases.get(alias, None)
        if _id is None:
            raise GeoJSONException("No such alias '%s'" % alias)
        res = [f for f in self.features if f.id == _id][0]
        return res if res else None

    def first(self) -> Feature | None:
        """
        Retrieves the first feature in the GeoJSON object

        Returns:
            Feature | None: The first feature in the GeoJSON object, None if the GeoJSON object has no features
        """
        return self.features[0] if self.features else None

    def last(self) -> Feature | None:
        """
        Retrieves the last feature in the GeoJSON object

        Returns:
            Feature | None: The last feature in the GeoJSON object, None if the GeoJSON object has no features
        """
        return self.features[-1] if self.features else None

    def load_json_object(self, obj: dict) -> None:
        """
        Loads data form a JSON object

        Args:
            obj: The JSON object to load
        """
        if "type" not in obj or obj["type"] != "FeatureCollection":
            raise GeoJSONException("Missing or invalid required key \"type\"!")

        for feature in obj["features"]:
            self.features.append(convert_feature(feature))

    def to_json(self) -> dict[str, Any]:
        """
        Converts the GeoJSON object to a JSON object

        Returns:
            object: The GeoJSON object as a JSON object
        """
        return {
            "type": self.type,
            "features": [f.to_json() for f in self.features]
        }

def convert_feature(feature):
    """
    Instantiates a feature from a JSON object

    Args:
        feature: The feature JSON object

    Returns:
        Feature: A feature instance
    """
    if feature is None:
        return Feature(None)

    f_type = feature["geometry"]["type"]
    if f_type == FeatureType.POINT:
        return Point(feature)
    elif f_type == FeatureType.MULTI_POINT:
        return MultiPoint(feature)
    elif f_type == FeatureType.LINE_STRING:
        return LineString(feature)
    elif f_type == FeatureType.MULTI_LINE_STRING:
        return MultiLineString(feature)
    elif f_type == FeatureType.POLYGON:
        return Polygon(feature)
    elif f_type == FeatureType.MULTI_POLYGON:
        return Polygon(feature)
    elif f_type == FeatureType.GEOMETRY_COLLECTION:
        return GeometryCollection(feature)
    return Feature(None)

def soft_update(obj_a: dict[str, Any], obj_b: dict[str, Any]):
    """
    Combines all objects shared between two objects, keeping any conflicting non-object values from obj_b

    Args:
        obj_a: An object to merge
        obj_b: An object to merge

    Returns:
        object: The merged object
    """
    obj = {}

    for key in obj_a.keys() | obj_b.keys():
        val_a = obj_a.get(key)
        val_b = obj_b.get(key)

        if isinstance(val_a, dict) and isinstance(val_b, dict):
            obj[key] = soft_update(val_a, val_b)
        elif key in obj_b:
            obj[key] = val_b
        else:
            obj[key] = val_a

    return obj

def soft_updates(*args: *tuple[dict[str, Any]]):
    obj = {}
    for curr in args:
        obj = soft_update(obj, curr)
    return obj

def compact_options(**kwargs: dict[str, Any]):
    return { key: _clean(value) for key, value in kwargs.items() if value is not None }

def _clean(value: str | int | float | bool | None | list | dict):
    if isinstance(value, dict):
        return { k: _clean(v) for k, v in value.items() if v is not None }
    return value

def add_not_empty(base: dict, key: str, value: str | int | float | bool | None | list | dict):
    """
    TODO
    """
    if value:
        base[key] = value
    return base
