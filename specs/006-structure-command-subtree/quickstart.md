# Quickstart: Structure Command Subtree Display

## Feature Overview

The enhanced `structure` command now accepts an optional Node ID to display only a specific subtree from your document hierarchy, helping you focus on particular sections without the visual clutter of the entire tree.

## Prerequisites

1. Prosemark installed: `pip install prosemark` or `uv pip install prosemark`
2. A project with an existing `_binder.md` file
3. Node IDs from your binder (visible in full structure output)

## Basic Usage

### Display Full Tree (Existing Behavior)
```bash
pmk structure
```

### Display Subtree from Specific Node
```bash
pmk structure 01997898-1dca-74d7-a727-b9a7023d0866
```

### Display Subtree in JSON Format
```bash
pmk structure --format json 01997898-1dca-74d7-a727-b9a7023d0866
```

## Test Scenarios

### Scenario 1: View Chapter and Its Scenes
**Setup**: You have a book with chapters containing scenes
**Command**:
```bash
pmk structure 01997898-1dca-74d7-a727-b9a7023d0866
```
**Expected Output**:
```
Project Structure:
1. The Director (01997898-1dca-74d7-a727-b9a7023d0866)
   ├─ ⇒ Academic—introducing Kolteo (01997898-1dcf-7bb2-806d-3c29d1ee5ed1)
   └─ ⇒ Kolteo—preparing to meet Julin (01997898-1dd1-719f-ad9f-ead37718612d)
```

### Scenario 2: Invalid Node ID Format
**Setup**: Provide non-UUID string
**Command**:
```bash
pmk structure abc123
```
**Expected Output**:
```
Error: Invalid node ID format: Invalid UUID format
```

### Scenario 3: Non-Existent Node
**Setup**: Valid UUID that doesn't exist in binder
**Command**:
```bash
pmk structure 550e8400-e29b-41d4-a716-446655440000
```
**Expected Output**:
```
Error: Node not found in binder: 550e8400-e29b-41d4-a716-446655440000
```

### Scenario 4: Empty Subtree (Leaf Node)
**Setup**: Node with no children
**Command**:
```bash
pmk structure 01997898-1dcf-7bb2-806d-3c29d1ee5ed1
```
**Expected Output**:
```
Project Structure:
⇒ Academic—introducing Kolteo (01997898-1dcf-7bb2-806d-3c29d1ee5ed1)
```

### Scenario 5: JSON Output for Subtree
**Setup**: Request JSON format for subtree
**Command**:
```bash
pmk structure --format json 01997898-1dca-74d7-a727-b9a7023d0866
```
**Expected Output**:
```json
{
  "roots": [
    {
      "display_title": "1. The Director",
      "node_id": "01997898-1dca-74d7-a727-b9a7023d0866",
      "children": [
        {
          "display_title": "⇒ Academic—introducing Kolteo",
          "node_id": "01997898-1dcf-7bb2-806d-3c29d1ee5ed1",
          "children": []
        },
        {
          "display_title": "⇒ Kolteo—preparing to meet Julin",
          "node_id": "01997898-1dd1-719f-ad9f-ead37718612d",
          "children": []
        }
      ]
    }
  ]
}
```

## Finding Node IDs

To find the Node ID of a section you want to focus on:

1. **Run full structure command**:
   ```bash
   pmk structure
   ```

2. **Look for the UUID in parentheses** after each item:
   ```
   1. The Director (01997898-1dca-74d7-a727-b9a7023d0866)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                    This is the Node ID
   ```

3. **Use in subtree command**:
   ```bash
   pmk structure 01997898-1dca-74d7-a727-b9a7023d0866
   ```

## Integration with Other Commands

The Node IDs displayed can be used with other Prosemark commands:
- `pmk edit <node_id>` - Edit a specific node
- `pmk remove <node_id>` - Remove a node from binder
- `pmk materialize <node_id>` - Export a subtree

## Troubleshooting

### "Binder file not found" Error
**Solution**: Ensure you're in a directory with `_binder.md` or use `--path`:
```bash
pmk structure --path /path/to/project 01997898-1dca-74d7-a727-b9a7023d0866
```

### Can't See Node IDs in Output
**Solution**: Node IDs are shown in parentheses. Placeholders without IDs show `[Placeholder]` instead.

### Performance with Large Trees
**Note**: The command uses best-effort performance. For very large trees (1000+ nodes), subtree display significantly improves responsiveness by limiting the traversal scope.

## Next Steps

- Use subtree display to focus on specific sections during editing
- Combine with `--format json` for programmatic processing
- Create scripts that operate on specific subtrees using Node IDs
