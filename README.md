# sphinx-hwreg

WIP, no APIs are "stable" in any sense

Sphinx domain to document embedded hardware SFRs.
Adds a `hwreg` domain to track register descriptions and
link to them.

## Using

Install via pip:

    pip install git+https://github.com/andreasWallner/sphinx-hwreg.git#<version hash that you want>


Add to your sphinx build by extending you `conf.py` with:

    import sphinx_hwreg
    extensions = [
      'sphinx_hwreg.hardware_registers',
    ]

To get nice visuals for the register field tables, a custom CSS needs to be added. For an example have a
look at `example/register-graphic.css`. Copy this to your static html folder and add via:

    html_static_path = ['_static']
    html_css_files = [
        'register-graphic.css',
    ]

## Directives

A short overview for the current directives:

### hwreg:automodule

Generates a full listing of all registers in a module, style depending on `type`.

Provide the name of the BusComponent as a parameter.

Options:

- `filename` path to the yaml file to load, relative to the documentation root dir
- `type` style to use, either `fancy` or `short`
- `noanchor` if present no anchors are generated - use this if the automodule is used
   as a second listing (e.g. in a register overview) so that links can go to a fuller description.
- `nowarn` do not generate a warning for e.g. a register w/o and fields

Example:

    .. hwreg:automodule:: PWM
       :filename: _generated/pwm.yaml
       :type: short
       :noanchor:
       :nowarn:

### hwreg:automodulesummary

Short list of all registers, linking to the register description if it exists. Does not contain any
information about the fields of the module.

Provide the name of the BusComponent as a parameter.

Options:

- `filename` path to the yaml file to load, relative to the documentation root dir

Example:

    .. hwreg:automodulesummary:: PWM
       :filename: _generated/pwm.yaml

### hwreg:autoreg

Generate register field graphic and field listing for a single register.

Provide the name of the BusComponent and Register as a parameter.

Options:

- `filename` path to the yaml file to load, relative to the documentation root dir
- `noanchor` if present no anchors are generated - use this if the automodule is used
   as a second listing (e.g. in a register overview) so that links can go to a fuller description.

Example:

    .. hwreg:autoreg:: PWM::level0
       :filename: _generated/pwm.yaml
       :noanchor:

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
