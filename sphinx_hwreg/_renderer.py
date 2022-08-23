from docutils import nodes
from sphinx import addnodes
from sphinx_hwreg._yaml_model import *
from docutils.nodes import Node
from typing import (IO, TYPE_CHECKING, Any, Callable, Dict, Generator, List, Optional, Set,
                    Tuple, Type, cast)

def entry(text, morecols=0, morerows=0):
  attributes = {}
  if morecols > 0:
    attributes['morecols'] = morecols
  if morerows > 0:
    attributes['morerows'] = morerows
  entry = nodes.entry(**attributes)
  if text is not None:
    if issubclass(type(text), nodes.Node):
      entry += text
    else:
      entry += nodes.paragraph(text=text)
  return entry

def render_register_list(component: BusComponent) -> List[Node]:
  table = nodes.table()
  table['classes'].append('register-list')
  tgroup = nodes.tgroup(cols=3)
  table += tgroup
  for i in range(3):
    tgroup += nodes.colspec()

  thead = nodes.thead()
  tgroup += thead
  head = nodes.row()
  for s in ['Name', 'Offset', 'Reset']:
    head += entry(s)
  thead += head

  tbody = nodes.tbody()
  tgroup += tbody

  for register in component.elements:
    row = nodes.row()
    row += entry(register.name)
    row += entry(f'0x{register.address:08x}')
    row += entry(f'0x{register.resetValue():08x}')
    tbody += row

  return table

def render_field_graphic(register: Register) -> List[Node]:
  table = nodes.table()
  table['classes'].append('register-field-graphic')
  tgroup = nodes.tgroup(cols=16)
  table += tgroup
  for i in range(16):
    tgroup += nodes.colspec(colwidth=5)

  tbody = nodes.tbody()
  tgroup += tbody

  head = nodes.row()
  tbody += head
  for i in range(31, 15, -1):
    head += entry(str(i))

  upper_row = nodes.row()
  last = 31
  for field in sorted(filter(lambda f: f.section.max > 15, register.fields), key=lambda f: -f.section.max):
    clipped_min = max(field.section.min, 16)
    if last > field.section.max:
      upper_row += entry(None, morecols=last-field.section.max-1)
    upper_row += entry(nodes.abbreviation(rawsource=field.name, text=field.name), morecols=field.section.max-clipped_min)
    last=clipped_min-1
  if last > 16:
    upper_row += entry(None, morecols=last-16)
  tbody += upper_row

  lower_row = nodes.row()
  last=15
  for field in sorted(filter(lambda f: f.section.min < 16, register.fields), key=lambda f: -f.section.max):
    clipped_max = min(field.section.max, 15)
    if last > clipped_max:
      lower_row += entry(None, morecols=last-clipped_max-1)
    p = nodes.paragraph()
    p += nodes.abbreviation(text=field.name, explanation=field.name)
    lower_row += entry(p, morecols=clipped_max-field.section.min)
    last = field.section.min-1
  if last > 0:
    lower_row += entry(None, morecols=last-1)
  tbody += lower_row
  
  foot = nodes.row()
  tbody += foot
  for i in range(15, -1, -1):
    foot += entry(str(i))

  return table

def render_field_table(register) -> List[Node]:
  table = nodes.table()
  table['classes'].append('register-field-table')
  tgroup = nodes.tgroup(cols=6)
  table += tgroup
  for w in [7, 3, 3, 3, 3, 30]:
    tgroup += nodes.colspec(colwidth=w)
  
  thead = nodes.thead()
  tgroup += thead
  row = nodes.row()
  row += entry('Name')
  row += entry('Bits')
  row += entry('Type')
  row += entry('Description', morecols=2)
  thead += row

  tbody = nodes.tbody()
  tgroup += tbody

  for field in register.fields:
    value_cnt = len(field.values or [])
    row = nodes.row()
    row += entry(field.name, morerows=value_cnt)
    row += entry(field.bits(), morerows=value_cnt)
    row += entry(field.accessType, morerows=value_cnt)
    row += entry(field.doc, morecols=2)
    tbody += row

    for value in field.values or []:
      row = nodes.row()
      row += entry(value.value)
      row += entry(value.name)
      row += entry(value.doc)
      tbody += row

  return table


def render_module_table(component: BusComponent) -> List[Node]:
  table = nodes.table()
  table['classes'].append('register-module-table')
  tgroup = nodes.tgroup(cols=9)
  table += tgroup
  for _ in range(9):
    tgroup += nodes.colspec()

  thead = nodes.thead()
  tgroup += thead
  row = nodes.row()
  for s in ['Offset', 'Name', 'Description', 'Width', 'Section', 'Field', 'R/W', 'Reset', 'Description']:
    row += entry(s)
  thead += row

  tbody = nodes.tbody()
  tgroup += tbody

  for reg in component.elements:
    first = True
    field_cnt = len(reg.fields)
    for field in reg.fields:
      row = nodes.row()
      if first:
        row += entry(f'0x{reg.address:04x}', morerows=field_cnt-1)
        row += entry(reg.name, morerows=field_cnt-1)
        row += entry(reg.doc, morerows=field_cnt-1)
        row += entry(component.dataWidth, morerows=field_cnt-1)
        first = False
      row += entry(field.bits())
      row += entry(field.name)
      row += entry(field.accessType)
      row += entry(f'0x{field.resetValue:x}')
      row += entry(field.doc)
      tbody += row

  return table