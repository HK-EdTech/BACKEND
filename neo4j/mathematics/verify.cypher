// Read-only verification queries for the mathematics graph.

SHOW CONSTRAINTS;

MATCH (n)
RETURN labels(n) AS node_type, count(n) AS total
ORDER BY node_type;

MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS total
ORDER BY relationship_type;

MATCH (n)
WITH labels(n) AS node_type, n.id AS entity_id, count(*) AS total
WHERE entity_id IS NOT NULL AND total > 1
RETURN node_type, entity_id, total
ORDER BY node_type, entity_id;

// Find prerequisite paths to the Factor Theorem.
MATCH path = (prerequisite)-[:PREREQUISITE_OF*1..5]->
  (target:Theorem {id: "theorem-factor-theorem"})
RETURN path;

// Find the knowledge context used by an AI answer.
MATCH (target:Theorem {id: "theorem-factor-theorem"})
OPTIONAL MATCH (target)-[:USES_FORMULA]->(formula:Formula)
OPTIONAL MATCH (target)-[:HAS_EXAMPLE]->(example:Example)
OPTIONAL MATCH (target)-[:HAS_MISCONCEPTION]->(misconception:Misconception)
OPTIONAL MATCH (target)-[:SUPPORTED_BY]->(source:Source)
RETURN target, formula, example, misconception, source;

// Find a learning route from algebraic expressions to the Factor Theorem.
MATCH path = (start:Concept {id: "concept-algebraic-expression"})
  -[:PREREQUISITE_OF*1..6]->
  (target:Theorem {id: "theorem-factor-theorem"})
RETURN path;
