from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective

from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, Index
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode
from sphinx.util.docutils import SphinxRole
from sphinx.util import logging
from sphinx.errors import ExtensionError
from docutils.parsers.rst.states import Inliner
from typing import Dict, List, Tuple
from docutils.nodes import Element, Node, system_message
from docutils.utils import Reporter, unescape
from sphinx_hwreg._yaml_model import *
from sphinx_hwreg._renderer import *
import os

import re

logger = logging.getLogger(__name__)


#def _parse(self, line):
#        """
#        Parses a single line/string for inline rst statements, like strong, emphasis, literal, ...
#
#        :param line: string to parse
#        :return: nodes
#        """
#        inline_parser = Inliner()
#        inline_parser.init_customizations(self.doc_settings)
#        result, message = inline_parser.parse(line, 0, self.doc_memo, self.dummy_doc)
#        if message:
#            raise SphinxNeedLayoutException(message)
#        return result 

class ManualRegisterDirective(ObjectDescription):
  """ Directive to manually add a register

  Expected is a headline of the format 'Name (id, hex-offset)'.
  Any content can be placed in the directive.
  """
  has_content = True
  required_arguments = 1

  def handle_signature(self, headline, signode):
    signode += addnodes.desc_name(text=headline)
    return headline
  
  def add_target_and_index(self, name_cls, headline, signode):
    reg_id = headline.split('(')[1].split(',')[0]
    s = reg_id.split('::')
    hwreg = self.env.get_domain('hwreg')
    signode['ids'].append(hwreg.add_register(s[0], s[1]))

  def transform_content(self, contentnode) -> None:
    contentnode.append(nodes.Text('this is some text coming from the code!'))
    xref = addnodes.pending_xref('', refdomain='hwreg', reftype='register', reftarget='radio::status', refexplicit=False)
    lit = nodes.literal()
    lit['classes'].append('xref')
    lit['classes'].append('hwreg')
    lit['classes'].append('hwreg-register')
    lit += nodes.Text('the problem case')
    xref.append(lit)
    p = nodes.paragraph()
    p += xref
    contentnode.append(p)

class ManualBitfieldRole(SphinxRole):
  name: str

  ref_re = re.compile('^(.+?)\s*(?<!\x00)<(.*?)>$')

  def __call__(self, name: str, rawtext: str, text: str, lineno: int,
               inliner: Inliner, options: Dict = {}, content: List[str] = None
               ) -> Tuple[List[Node], List[system_message]]:
    matched = self.ref_re.match(unescape(text))
    if matched:
      self.bitfield_name = unescape(matched.group(1))
      self.register_name = unescape(matched.group(2))
    else:
      raise Exception(f'invalid hwreg bitfield definition: {text}')
    return super().__call__(name, rawtext, text, lineno, inliner, options, content)
  
  def run(self) -> Tuple[List[Node], List[system_message]]:
    hwreg = self.env.get_domain('hwreg')
    s = self.register_name.split('::')
    targetid = hwreg.add_bitfield(s[0], s[1], self.bitfield_name)
    targetnode = nodes.target('', self.bitfield_name, ids=[targetid])
    return ([targetnode], [])


class AutoRegisterDirective(ObjectDescription):
  """ 
  Add register documentation to documentation,
  the content of the directive is placed as a description.
  """
  has_content = True
  option_spec = {
    'filename': lambda x: x,
    'noanchor': lambda _: True
  }

  _yaml = None

  def handle_signature(self, sig, signode):
    (self._component, self._register) = sig.split('::')
    signode += addnodes.desc_name(text=f'{self._component}::{self._register}')
    # TODO error handling
  
  def add_target_and_index(self, name_cls, headline, signode):
    hwreg = self.env.get_domain('hwreg')
    if not self.options.get('noanchor', False):
      signode['ids'].append(hwreg.add_register(self._component, self._register))

  def transform_content(self, contentnode) -> None:
    hwreg = self.env.get_domain('hwreg')
    register = hwreg.get_register(self._component, self._register, self.options.get('filename', None))
    if register.doc is not None:
      contentnode.append(nodes.paragraph(text=register.doc)) # TODO parse
    contentnode.append(render_field_graphic(register))
    contentnode.append(render_field_table(register))


class AutoModuleSummary(ObjectDescription):
  """
  Generates a list of all registers in a component.

  With type 'full' a list will all fields is generated,
  while 'list' (default) generates only an overview with
  name, reset value and offset.
  """
  has_content = False
  option_spec = {
    'filename': lambda x: x,
  }

  def handle_signature(self, sig, signode):
    signode += addnodes.desc_name(text=f'{sig}')
  
  def transform_content(self, contentnode) -> None:
    hwreg = self.env.get_domain('hwreg') #type: HardwareRegisterDomain
    component = hwreg.get_component(self.get_signatures()[0], self.options.get('filename', None))
    contentnode += render_register_list(component, hwreg.make_register_xref)


class AutoModuleDirective(ObjectDescription):
  """
  Add all registers of a module to the documentation.
  """
  has_content = False
  option_spec = {
    'filename': lambda x: x,
    'type': lambda x: x, # TODO check?
    'noanchor': lambda _: True,
  }

  def handle_signature(self, sig, signode):
    pass

  # TODO generate multiple desc nodes
  def transform_content(self, contentnode) -> None:
    sig = self.get_signatures()[0]
    hwreg = self.env.get_domain('hwreg') #type: HardwareRegisterDomain
    noanchor = self.options.get('noanchor', False)
    component = hwreg.get_component(sig, self.options.get('filename', None))
    type = self.options.get('type', 'fancy')
    if type == 'short':
      contentnode += render_module_table(component, None, hwreg.add_register if not noanchor else None)

    elif type == 'fancy':
      for reg in component.elements:
        headline = addnodes.desc_name(text=f'{sig}::{reg.name}')
        if not self.options.get('noanchor', False):
          headline['ids'].append(hwreg.add_register(component.busComponentName, reg.name))
        contentnode.append(headline)
        if reg.fields is not None:
          contentnode.append(render_field_graphic(reg))
          contentnode.append(render_field_table(reg))
        else:
          logger.warning(f'hwreg::automodule {sig}.{reg.name} does not have any fields in it')

    else:
      raise Exception(f'Invalid AutoModule type {type}')


class HardwareRegisterDomain(Domain):
  name = 'hwreg'
  label = 'Hardware Registers'
  roles = {
    'register': XRefRole(),
    'bitfield': XRefRole(),
    'define-bf': ManualBitfieldRole(),
  }
  directives = {
    'define-reg': ManualRegisterDirective,
    'autoreg': AutoRegisterDirective,
    'automodule': AutoModuleDirective,
    'automodulesummary': AutoModuleSummary,
  }
  initial_data = {
    'registers': [],
    'bitfields': [],
  }

  yaml_cache = {}

  def get_full_qualified_name(self, node):
    return '{}.{}'.format('recipe', node.arguments[0])

  def get_objects(self):
    yield from self.data['registers']
    yield from self.data['bitfields']
  
  def get_type_name(self, type, primary):
    if type == 'registers':
      return 'Register'
    elif type == 'bitfields':
      return 'Bitfield'

  def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
    if typ == 'register':
      match = [(docname, anchor) for reg_id, dispname, type, docname, anchor, prio in self.data['registers'] if reg_id == target]
    else: # typ == 'bitfield'
      match = [(docname, anchor) for bitfield_id, dispname, type, docname, anchor, prio in self.data['bitfields'] if bitfield_id == target]

    if len(match) > 0:
      (todocname, targ) = match[0]
      return make_refnode(builder, fromdocname, todocname, targ, contnode, targ)
    else:
      logger.warn(f'could not resolve xref {target} in {fromdocname}')
      return None

  def add_register(self, module, register):
    reg_id = f'{module}::{register}'
    anchor = f'hwreg-register-{module}-{register}'
    self.data['registers'].append((reg_id, reg_id, 'register', self.env.docname, anchor, 1))
    return anchor
  
  def add_bitfield(self, module, register, bitfield):
    bf_id = f'{module}::{register}::{bitfield}'
    anchor = f'hwreg-bitfield-{module}-{register}-{bitfield}'
    self.data['bitfields'].append((bf_id, bitfield, 'bitfield', self.env.docname, anchor, 1))
    return anchor
  
  def get_register(self, moduleName, registerName, filename=None) -> Register:
    component = self.get_component(moduleName, filename)
    register = next((r for r in component.elements if r.name == registerName), None)
    if register is None:
      raise ExtensionError(f'Could not find register {moduleName}::{registerName}', modname='hwreg')
    return register
  
  def get_component(self, moduleName, filename=None) -> BusComponent:
    if filename is not None and filename not in self.yaml_cache:
      filename = os.path.abspath(filename) #TODO abspath relative to rst file being processed
      with open(filename) as f:
        self.yaml_cache[filename] = yaml.load(f, Loader=yaml.UnsafeLoader)
    elif filename is None:
      pass
  
    valid_files = self.yaml_cache.values() if filename is None else [self.yaml_cache[filename]]
    busComponent = next((bc for bc in valid_files if bc.busComponentName == moduleName), None)

    if busComponent is None:
      raise ExtensionError(f'Could not find component {moduleName}', modname='hwreg')
    return busComponent
  
  def make_register_xref(self, node: Node, component: str, register: str) -> Node:
    target = f'{component}::{register}'
    para = nodes.paragraph()
    xref = addnodes.pending_xref('', refdomain='hwreg', reftype='register', reftarget=target, refexplicit=False)
    if node is None:
      lit = nodes.literal()
      lit['classes'].append('xref')
      lit['classes'].append('hwreg')
      lit['classes'].append('hwreg-register')
      text = nodes.Text(target)

      lit += text
      xref += lit
    else:
      xref += node

    para += xref
    return xref
  
  def make_bitfield_xref(self, node: Node, component: str, register: str, field: str) -> Node:
    target = f'{component}::{register}::{field}'
    p = nodes.paragraph()
    xref = addnodes.panding_xref('', refomain='hwreg', reftype='field', reftarget=target, refexplicit=False)
    if node is None:
      lit = nodes.literal()
      lit['classes'].append('xref')
      lit['classes'].append('hwreg')
      lit['classes'].append('hwreg-field')
      text = nodes.Text(target)
  
      lit += text
      xref += lit
    else:
      xref += node

    p += xref
    return xref


def setup(app):
  app.add_domain(HardwareRegisterDomain)

  return {
    'version': '0.1',
    'parallel_read_safe': True,
    'parallel_write_safe': True,
  }
