# Tutorial 2: Your First Flow — Hello World

**What you'll learn:** Create a project, add nodes, wire them, edit properties, and run.

**Prerequisites:** Tutorial 1.

### Steps

1. **Create a project**
   - File > New Project…
   - Name: `hello_world`, location: any folder
   - Click **Create**

2. **Open the graph**
   - In Project Explorer, double-click `graphs/main.pfcgraph.yaml`
   - The canvas appears (empty)

3. **Add a Start node**
   - In Component Palette, drag **Start Node** onto the canvas
   - A blue-bordered node labelled "Start Node" appears
   - Single-click it to select it
   - In Object Inspector, change **Title** to `Start` (click the blue value field, type, press Enter)

4. **Add an LLM Prompt node**
   - Drag **LLM Prompt Node** from the palette onto the canvas, to the right of Start
   - Single-click it; set **Title** to `Ask LLM`
   - Set **prompt_file** to `prompts/hello.md`

5. **Add a Stop node**
   - Drag **Stop Node** to the right of Ask LLM
   - Set **Title** to `End`

6. **Auto-layout** (optional, to tidy positions)
   - View > Auto Layout (Ctrl+Shift+L)
   - View > Zoom to Fit (Ctrl+0)

7. **Create the prompt file**
   - Project Explorer > right-click `prompts` folder > New File (or create manually)
   - Or: open the **Markdown** tab at bottom, type: `Say hello to the world in one sentence.`
   - Save (Ctrl+S) to `prompts/hello.md`

8. **Validate the graph**
   - Project > Validate Project (Ctrl+Shift+V)
   - Problems tab shows any errors (red border on nodes with issues)

9. **Run with mock provider**
   - Run > Run Active Flow (F5)
   - Check **Run Log** tab — you'll see one step per node

**Expected result:** Three nodes on canvas, green (no error badges), run log shows Start → Ask LLM → End.

---
