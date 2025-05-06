import xml.etree.ElementTree as ET
import json
from xml.dom import minidom


class UMLClass:
    def __init__(self, name, is_root, documentation):
        self.name = name
        self.is_root = is_root
        self.documentation = documentation
        self.attributes = []

    
    def add_attribute(self, name, attribute_type):
        self.attributes.append({"name": name, "type": attribute_type})
    

class Aggregation:
    def __init__(self, source, target, source_multiplicity, target_multiplicity):
        self.source = source
        self.target = target
        self.source_multiplicity = source_multiplicity
        self.target_multiplicity = target_multiplicity


    def parse_multiplicity(self, multiplicity):
        if ".." in multiplicity:
            start, end = multiplicity.split("..")
            return int(start), int(end)
        
        value = int(multiplicity)
        return value, value


    def get_source_range(self):
        return self.parse_multiplicity(self.source_multiplicity)


    def get_target_range(self):
        return self.parse_multiplicity(self.target_multiplicity)


class UMLModel:
    def __init__(self):
        self.classes = {}
        self.aggregations = []


    def load_from_xml(self, filename):
        tree = ET.parse(filename, parser=None)
        root = tree.getroot()

        for elem in root.findall("Class"):
            name = elem.attrib["name"]
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


    def generate_config_xml(self, filename):
        root_class = next((cls for cls in self.classes.values() if cls.is_root), None)
        if not root_class:
            raise ValueError("Не найден корневой класс (is_root=True)")
        
        def build_xml_element(class_name):
            uml_class = self.classes[class_name]
            element = ET.Element(uml_class.name)

            for attr in uml_class.attributes:
                attr_element = ET.SubElement(element, attr["name"])
                attr_element.text = attr["type"]
                #print(f"Added attribute: {attr['name']}")

            for aggr in self.aggregations:
                if aggr.target == class_name:
                    child_element = build_xml_element(aggr.source)
                    element.append(child_element)

            return element
        
        root_element = build_xml_element(root_class.name)

        rough_string = ET.tostring(root_element, "unicode")
        reparsed = minidom.parseString(rough_string)
        result_xml = reparsed.toprettyxml(indent="    ")

        with open(filename, "w") as file:
            file.write(result_xml)

            
    def generate_meta_json(self, filename):
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

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(meta, file, indent=4)

        
if __name__ == "__main__":
    input_file = "test_input.xml" 
    output_config_xml_file = "./out/config.xml"
    output_meta_json_file = "./out/meta.json"

    model = UMLModel()
    model.load_from_xml(input_file)
    model.generate_config_xml(output_config_xml_file)
    model.generate_meta_json(output_meta_json_file)
