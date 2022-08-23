import yaml

# use dataclasses? https://stackoverflow.com/questions/71301407/pyyaml-support-for-default-list-in-dataclass
class BusComponent(yaml.YAMLObject):
  yaml_tag = '!BusComponent;1'
  def __init__(self, busComponentName, dataWidth, wordAddressInc, elements):
    self.busComponentName = busComponentName
    self.dataWidth = dataWidth
    self.wordAddressInc = wordAddressInc
    self.elements = elements

class Register(yaml.YAMLObject):
  yaml_tag = '!Register;1'
  def __init__(self, name, doc, address, fields):
    self.name = name
    self.doc = doc
    self.address = address
    self.fields = fields
  
  def resetValue(self):
    return sum([f.resetValue for f in self.fields or []])

class Field(yaml.YAMLObject):
  yaml_tag = '!Field;1'
  def __init__(self, name, doc, datatype, section, accessType, resetValue, readError, values):
    self.name = name
    self.doc = doc
    self.datatype = datatype
    self.section = section
    self.accessType = accessType
    self.resetValue = resetValue
    self.readError = readError
    self.values = values
  
  def bits(self):
    if self.section.max == self.section.min:
      return f'{self.section.min}'
    return f'{self.section.max}:{self.section.min}'

class Section(yaml.YAMLObject):
  yaml_tag = '!Section;1'
  def __init__(self, min, max):
    self.min = min
    self.max = max

class Value(yaml.YAMLObject):
  yaml_tag = '!Value;1'
  def __init__(self, name, value, doc):
    self.name = name
    self.value = value
    self.doc = doc
