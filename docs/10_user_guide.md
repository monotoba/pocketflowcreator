# User Guide

## Create a Workflow

1. Create a new project.
2. Choose a starting template or blank flow.
3. Drag a node type from the Component Palette onto the graph.
4. Select the node and edit its properties in the Object Inspector.
5. Add or confirm action ports.
6. Wire action ports to destination nodes.
7. Validate the flow.
8. Run or debug the flow.
9. Export the project as Python PocketFlow code.

## Edit a Prompt

1. Select an LLM node.
2. Open the Prompt section in the Object Inspector.
3. Click Edit Prompt.
4. Use Insert Variable to add shared-store variables.
5. Preview the rendered prompt.
6. Test with mock or real provider.

## Create a Custom Node Type

1. Choose Node -> New Custom Node Type.
2. Select a base type.
3. Define properties, actions, reads, and writes.
4. Choose generated, lifecycle-hook, or full custom Python mode.
5. Generate skeleton code if needed.
6. Validate the node type.
7. Use it from the Component Palette.
