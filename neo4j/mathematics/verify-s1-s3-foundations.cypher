// Verification queries for the S1-S3 foundation expansion.

// Count nodes by label.
MATCH (n)
RETURN labels(n) AS node_type, count(n) AS total
ORDER BY node_type;

// Count relationships by type.
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS total
ORDER BY relationship_type;

// Check duplicate IDs.
MATCH (n)
WITH labels(n) AS node_type, n.id AS entity_id, count(*) AS total
WHERE entity_id IS NOT NULL AND total > 1
RETURN node_type, entity_id, total
ORDER BY node_type, entity_id;

// Find a foundation path to the existing polynomial concept.
MATCH path = (start:Concept {id: "concept-integer"})
  -[:PREREQUISITE_OF*1..8]->
  (target:Concept {id: "concept-polynomial"})
RETURN path;

// Find a path from linear equations to polynomial equations.
MATCH path = (start:Concept {id: "concept-linear-equation"})
  -[:PREREQUISITE_OF*1..5]->
  (target:Concept {id: "concept-polynomial-equation"})
RETURN path;

// Return concepts that can support an AI answer about a linear graph.
MATCH (target:Concept {id: "concept-linear-graph"})
OPTIONAL MATCH (prerequisite)-[:PREREQUISITE_OF]->(target)
OPTIONAL MATCH (related)-[:RELATED_TO]-(target)
RETURN target, collect(DISTINCT prerequisite) AS prerequisites,
       collect(DISTINCT related) AS related_concepts;
