import xml.etree.ElementTree as ET
import json
from xml.dom import minidom


class UMLClass:
    def __init__(self, name: str, is_root: bool, documentation: str):
        self.name = name
        self.is_root = is_root
        self.documentation = documentation
        self.attributes = []

    
    def add_attribute(self, name, attribute_type):
        self.attributes.append({"name": name, "type": attribute_type})
    

class Aggregation:
    def __init__(self, source: str, target: str, source_multiplicity: str, target_multiplicity: str):
        self.source = source
        self.target = target
        self.source_multiplicity = source_multiplicity
        self.target_multiplicity = target_multiplicity


    def parse_multiplicity(self, multiplicity: str):
        try:
            if ".." in multiplicity:
                start, end = multiplicity.split("..")
                return int(start), int(end)
        
            value = int(multiplicity)
            return value, value
        except ValueError:
            raise ValueError(f"Invalid multiplicity format: {multiplicity}")


    def get_source_range(self):
        return self.parse_multiplicity(self.source_multiplicity)


    def get_target_range(self):
        return self.parse_multiplicity(self.target_multiplicity)


class UMLModel:
    def __init__(self):
        self.classes = {}
        self.aggregations = []


    def load_from_xml(self, filename: str):
        try:
            tree = ET.parse(filename, parser=None)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML file: {e}")
        
        root = tree.getroot()

        for elem in root.findall("Class"):            
            name = elem.attrib["name"]
            if name in self.classes:
                raise ValueError(f"Duplicate class name: {name}")

            is_root = elem.attrib.get("isRoot", "false").lower() == "true"
            documentation = elem.attrib.get("documentation", "")
            uml_class = UMLClass(name, is_root, documentation)

            for attr in elem.findall("Attribute"):
                uml_class.add_attribute(attr.attrib["name"], attr.attrib["type"])
            
            self.classes[name] = uml_class

        for aggr in root.findall("Aggregation"):
            self.aggregations.append(Aggregation(
                aggr.attrib["source"],
                aggr.attrib["target"],
                aggr.attrib["sourceMultiplicity"],
                aggr.attrib["targetMultiplicity"]
            ))


    def _build_xml_element(self, class_name: str):
        uml_class = self.classes[class_name]
        element = ET.Element(uml_class.name)

        for attr in uml_class.attributes:
            attr_element = ET.SubElement(element, attr["name"])
            attr_element.text = attr["type"]

        for aggr in self.aggregations:
            if aggr.target == class_name:
                child_element = self._build_xml_element(aggr.source)
                element.append(child_element)

        if len(element) == 0:
            element.text = "\n" + "    " 

        return element


    def generate_config_xml(self, filename: str):
        root_class = next((cls for cls in self.classes.values() if cls.is_root), None)
        if not root_class:
            raise ValueError("Root element was not found")
        
        root_element = self._build_xml_element(root_class.name)

        try:
            rough_string = ET.tostring(root_element)
            reparsed_string = minidom.parseString(rough_string)
            result_xml = reparsed_string.toprettyxml(indent="\t")
        except Exception as e:
            raise ValueError(f"XML generation error: {e}")

        try:
            with open(filename, "w") as file:
                file.write(result_xml)
        except IOError as e:
            raise IOError(f"Failed to write XML file: {e}")

            
    def generate_meta_json(self, filename: str):
        meta = []
        for class_name, cls in self.classes.items():
            entry = {
                "class": class_name,
                "documentation": cls.documentation,
                "isRoot": cls.is_root,
            }

            for aggr in self.aggregations:
                if aggr.source == class_name:
                    min_val, max_val = aggr.get_source_range()
                    entry["max"] = str(max_val)
                    entry["min"] = str(min_val)
                    break

            entry["parameters"] = []

            for attr in cls.attributes:
                entry["parameters"].append({
                    "name": attr["name"],
                    "type": attr["type"]
                })

            for aggr in self.aggregations:
                if aggr.target == class_name:
                    entry["parameters"].append({
                        "name": aggr.source,
                        "type": "class"
                    })            

            meta.append(entry)

        try:
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(meta, file, indent=4)
        except IOError as e:
            raise IOError(f"Failed to write JSON file: {e}")

        
if __name__ == "__main__":
    try:
        input_file = "test_input.xml" 
        output_config_xml_file = "./out/config.xml"
        output_meta_json_file = "./out/meta.json"

        model = UMLModel()
        model.load_from_xml(input_file)
        model.generate_config_xml(output_config_xml_file)
        model.generate_meta_json(output_meta_json_file)

    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except ValueError as e:
        print(f"Value error: {e}")
    except IOError as e:
        print(f"I/O error: {e}")
    except Exception as e:
        print(f"Error: {e}")
