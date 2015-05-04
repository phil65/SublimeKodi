# SublimeKodi
ST3 plugin to show translated Kodi labels in mouseover popup, quickly open the Kodi log, log syntax highlighting and much more.

**Note:** Sublime Text 2 is not supported.  Also, SublimeKodi takes advantage of certain features of ST3 that have bugs in earlier ST3 releases or were implemented during betas.  For the best experience, use the latest ST3 dev build.

Feature list:


Kodi Log:

- Open log from command palette
- Added syntax highlighting
- Jump to code where exception ocurred by pressing shift+enter when line with path is selected


Tooltips:

- Show english translation when label id is selected
- Show additional translation of choice when label id is selected
- show color hex value for color names
- show variable content
- show include content
- show font tag
- show constant value
- show value of selected Kodi InfoLabel in tooltip (by using JSON-RPC)
- show infos for selected image (image dimensions and file size)


JSON-RPC: (newest script.toolbox version needed)

- auto-reload skin after saving xml
- Execute builtins from command palette


Shortcuts:

- jump to include (shift+enter)
- jump to variable (shift+enter)
- jump to constant (shift+enter)
- jump to font (shift+enter)
- jump to label definition (shift+enter)
- jump to color definition (shift+enter)
- preview skin image (ctrl+enter)


Fuzzy searches:

- Search through all skin labels
- Search through all textures including preview
- Search though all available fonts


Context menu:

- "move label to language file" (creates entry in strings.po using the first free id and replaces selected text with $LOCAIZE[])

