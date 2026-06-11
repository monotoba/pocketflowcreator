# Tutorial 18: Validation and Error Badges

**What you'll learn:** Use the validator to find graph problems before running.

### Common Validation Errors

| Error Code | Meaning | Fix |
|---|---|---|
| PFCE1001 | No start node set | Mark a node as the flow's start node |
| PFCE1002 | Duplicate node IDs | Delete and re-add the duplicate node |
| PFCE1003 | Start node ID doesn't exist | Re-set the start node |
| PFCE2001 | Edge source node missing | Re-wire or delete the dangling edge |
| PFCE2002 | Edge destination node missing | Re-wire or delete the dangling edge |
| PFCE2003 | Edge has no action label | Add an action label to the edge |
| PFCE2101 | Action not declared on source node | Add the action to the node's Actions field |
| PFCE2102 | Subflow node missing `subflow_ref` | Set `subflow_ref` in Inspector |

### Steps

1. Create a new project, add a Basic Node, leave it unwired
2. Project > Validate Project (Ctrl+Shift+V) — observe errors in the Problems tab
3. Notice red border badges on the canvas nodes with errors
4. Fix each error by editing properties or adding edges
5. Re-validate — badges clear when all errors are resolved

---
