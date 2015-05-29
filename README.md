# SublimeKodi

[![Join the chat at https://gitter.im/phil65/SublimeKodi](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/phil65/SublimeKodi?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

ST3 plugin to show translated Kodi labels in mouseover popup, quickly open the Kodi log, log syntax highlighting and much more.


### Requirements

In order to get everything working you need to manage your Kodi add-ons as a project while havin the add-on root as the only project folder.
To allow JSON-RPC interaction with Kodi you also need to install script toolbox ( https://github.com/phil65/script.toolbox ) as well as activating JSON control via Kodi settings.
Also, don´t forget to set up your SublimeKodi settings!

### Feature list:

##### Kodi Log:

- Open log from command palette
- Jump to code where exception ocurred by pressing shift+enter when line with path is selected


##### Syntax Highlighting:

- Added custom syntax highlighting for
  - Kodi language files
  - Kodi SkinXML files
  - Kodi log files


##### Tooltips:

- Show english translation when label id is selected
- Show additional translation of choice when label id is selected
- Show actual color / color hex / alpha % for all color themes when color is selected
- Show variable content
- Show include content
- Show font tag
- Show constant value
- Show value of selected Kodi InfoLabel in tooltip (by using JSON-RPC)
- Show infos for selected image (image dimensions and file size)
- Show window file name


##### JSON-RPC: (newest script.toolbox version needed)

- Auto-reload skin after saving xml
- Execute builtins from command palette
- Reload skin
- Display Kodi InfoLabel


##### Shortcuts:

- Auto-completion for common Kodi snippets
  - builtins
  - boolean conditions
  - window names
  - include names
  - variable names
  - font names
  - constant names


##### Shortcuts:

- Jump to include (shift+enter)
- Jump to variable (shift+enter)
- Jump to constant (shift+enter)
- Jump to font (shift+enter)
- Jump to label definition (shift+enter)
- Jump to color definition (shift+enter)
- Preview skin image (ctrl+enter)
- Switch xml folder (ctrl+shift+enter)


##### Fuzzy searches:

- Search through all skin labels
- Search through all textures including preview
- Search through all available fonts
- Search through all translated strings ($LOCALIZE[id]) of currently open file
- Search through all boolean conditions
- Search through all builtins


##### Sanity checks:

- Check for unused includes / invalid include references
- Check for unused variables / invalid variable references
- Check for unused fonts / invalid include font references
- Check for unused labels / invalid label references
- Check for invalid values / structure:
  - invalid nodes
  - invalid attributes
  - invalid attribute values
  - invalid node values
  - invalid multiple nodes
  - check for correct parantheses
  - check "empty" action calls


##### Context menu:

- Move label to language file (creates entry in strings.po using the first free id and replaces selected text with $LOCALIZE[foo])
- Go to Kodi online wiki (opens corresponding online help page, only for control types atm)
- Preview skin image


##### Misc:

- Auto-check skin file on saving
- Create element row (and insert ascending number starting with [offset]) for quickly multiplying listitems / buttons
- SkinCheck can also be used from command line with "python script.py PATH_TO_ADDON"
  - requires Python 3.3 interpreter
- Build skin with texturepacker from command palette
- Jump-to-Addon command


##### Remote Actions

- Quick access to common ADB commands:
  - set remote IP
  - connect to remote
  - push add-on to remote
  - pull log from remote
  - clear temp folder on remote
  - pull screenshot from remote
  - reboot remote

___

**Note:** *Sublime Text 2 is not supported.  Also, SublimeKodi takes advantage of certain features of ST3 that have bugs in earlier ST3 releases or were implemented during betas.  For the best experience, use the latest ST3 dev build. Minimum required version is build 3084.*

