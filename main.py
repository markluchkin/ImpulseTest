import xml.etree.ElementTree as ET
import xml.dom.minidom
import json


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


    def to_dict(self):
        return {
            "source": self.source,
            "target": self.target,
            "sourceMultiplicity": self.source_multiplicity,
            "targetMultiplicity": self.target_multiplicity 
        }


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
        ...

            
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
    output_config_xml_file = "config.xml"
    output_meta_json_file = "meta.json"

    model = UMLModel()
    model.load_from_xml(input_file)
    model.generate_config_xml(output_config_xml_file)
    model.generate_meta_json(output_meta_json_file)
