# sphinx-hwreg

WIP, no APIs are "stable" in any sense

Sphinx domain to document embedded hardware SFRs.
Adds a `hwreg` domain to track register descriptions and
link to them.

## Example manual usage

To use the module for cross references only, directives and roles exist
to add registers to the `hwreg` domain.

    .. hwreg:define-reg:: Status (radio::status, 0x0014)
    
       .. ext-table:: Some text...
    
          * - :hwreg:define-bf:`TX <radio::status>`
            - this is another
          * - foo
            - bar
    
       This would then be a text that should also be inside the directive
    
    Somewhere else we can link back to the register :hwreg:register:`radio::status` with it's :hwreg:bitfield:`radio::status::TX`