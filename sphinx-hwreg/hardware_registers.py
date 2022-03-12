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
from docutils.parsers.rst.states import Inliner
from typing import (IO, TYPE_CHECKING, Any, Callable, Dict, Generator, List, Optional, Set,
                    Tuple, Type, cast)
from docutils.nodes import Element, Node, system_message
from docutils.utils import Reporter, unescape

import re

logger = logging.getLogger(__name__)


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
    hwreg = self.env.get_domain('hwreg')
    signode['ids'].append(hwreg.add_register(reg_id, headline))


class ManualBitfieldRole(SphinxRole):
  name: str

  ref_re = re.compile('^(.+?)\s*(?<!\x00)<(.*?)>$')

  def __call__(self, name: str, rawtext: str, text: str, lineno: int,
               inliner: Inliner, options: Dict = {}, content: List[str] = None
               ) -> Tuple[List[Node], List[system_message]]:
    matched = self.ref_re.match(unescape(text))
    print(unescape(text), matched.group(1), matched.group(2))
    if matched:
      self.bitfield_name = unescape(matched.group(1))
      self.register_name = unescape(matched.group(2))
    else:
      raise Exception(f'invalid hwreg bitfield definition: {text}')
    return super().__call__(name, rawtext, text, lineno, inliner, options, content)
  
  def run(self) -> Tuple[List[Node], List[system_message]]:
    print(self.name, self.rawtext, self.text, self.content, self.options)
    hwreg = self.env.get_domain('hwreg')
    targetid = hwreg.add_bitfield(self.bitfield_name, self.register_name)
    targetnode = nodes.target('', self.bitfield_name, ids=[targetid])
    return [[targetnode], []]


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
  }
  initial_data = {
    'registers': [],
    'bitfields': [],
  }

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
      logger.warn(f'could not resolve xref to register "{target}" in {fromdocname}')
      return None

  def add_register(self, reg_id, headline):
    anchor = 'hwreg-register-{}'.format(reg_id.replace('::', '-'))

    self.data['registers'].append((reg_id, headline, 'register', self.env.docname, anchor, 1))
    return anchor
  
  def add_bitfield(self, bitfield, reg_id):
    anchor = 'hwreg-bitfield-{}-{}'.format(reg_id.replace('::', '-'), bitfield)

    self.data['bitfields'].append((f'{reg_id}::{bitfield}', bitfield, 'bitfield', self.env.docname, anchor, 1))
    return anchor
  

def setup(app):
  app.add_domain(HardwareRegisterDomain)

  return {
    'version': '0.1',
    'parallel_read_safe': True,
    'parallel_write_safe': True,
  }