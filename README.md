**Pandoc GUI from YAML**

A graphical user interface for the Pandoc command-line utility, a powerful document converter between various markup and office file formats.

**Description**

Pandoc GUI from YAML is a Python application built with the Tkinter library that simplifies working with Pandoc by allowing users to configure conversion options through an intuitive visual interface—without memorizing complex command-line syntax.

- Visually configure Pandoc options without needing to recall command-line syntax.
- Automatically detect the input format (--from) based on the input file extension (e.g., .docx → docx, .md → markdown).
- Dynamically generate the output filename next to the source file, with the correct extension based on the selected output format (--to).
- Filter options by popularity level (1 to 5); by default, only the most commonly used options (popularity ≥ 4) are shown.
- The command field is fully editable, the exact command displayed is executed upon launch.
- Manually edit the final command before execution, whatever appears in the command field will be run.
- The command updates automatically when any parameter changes.
- Mouse wheel scrolling works only inside the parameters panel, file selection and the command field remain always visible.
- Full support for all Pandoc options via the configuration file pandoc_options.yaml.
- Supports all major formats: Markdown, HTML, LaTeX, Word (.docx), EPUB, PDF, Jupyter Notebook, and more.

------------------------------------------------------------------------

**Key Features**

- Automatic --from detection based on input file extension.
- Dynamic output filename, saved alongside the source file, with an extension matching --to.
- Parameter filtering, only relevant options shown by default (popularity ≥ 4).
- Editable command, manual adjustments allowed before execution.
- Complete Pandoc option coverage via pandoc_options.yaml.py.
- Mouse wheel scrolls only the parameters section.
- Supports all formats: Markdown, HTML, LaTeX, Word (.docx), EPUB, PDF, Jupyter Notebook, etc.

**Requirements**

- Python 3.7 or newer
- Pandoc installed (version 2.0 or later)
- Python dependencies:
    - pyyaml

------------------------------------------------------------------------

**Project Structure**

- 1_pandoc_download.bat # Downloads the official Pandoc installer
- 2_python_portable_download.bat # Downloads portable Python (for portability)
- 3_python_install_requirements.bat # Installs required packages (pyyaml)
- 4_python_check_install_requirements.bat # Verifies that dependencies are installed
- 5_run_pandoc_gui_from_yaml.yaml # Launches the application (YAML-based runner)
- pandoc.exe # Pandoc binary (included for portability)
- pandoc_gui_from_yaml.py # Main GUI executable
- pandoc_options.yaml.py # Pandoc options definition (as a Python dictionary)
- README.md # Documentation

**How to Run**

Execute the following batch files in order:

1. 1_pandoc_download.bat → downloads Pandoc
2. 2_python_portable_download.bat → downloads portable Python
3. 3_python_install_requirements.bat → installs the pyyaml package
4. 4_python_check_install_requirements.bat → confirms all dependencies are present
5. 5_run_pandoc_gui_from_yaml.yaml → launches the application

**Interface**

- Top panel: input file selection + “Popularity ≥ [1–5]” filter
- Command field: editable with word wrap, executed when you click “Convert”
- Scrollable parameters panel: options grouped by category (input/output, PDF, citations, metadata, etc.)
- “Convert” button: runs the exact command shown in the command field

**Notes**

- On first launch, only the most popular options (popularity ≥ 4) are displayed.
- To view all options, select “1” in the “Popularity ≥” dropdown menu.
- The command updates automatically, unless you manually edit the command field, which disables auto-updating.
- If you change any parameter after manual editing, the command resets to the auto-generated version.

**Support**

This application is based on the official Pandoc documentation: [Pandoc User's Guide](https://pandoc.org/MANUAL.html)

**License**

This project is provided "as is" with no restrictions. Feel free to use, modify, and distribute it at your discretion.