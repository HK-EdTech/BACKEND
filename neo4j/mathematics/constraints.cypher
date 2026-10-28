// Stable IDs prevent duplicate entities across imports.

CREATE CONSTRAINT stage_id_unique IF NOT EXISTS
FOR (n:Stage)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT grade_id_unique IF NOT EXISTS
FOR (n:Grade)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT strand_id_unique IF NOT EXISTS
FOR (n:Strand)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT topic_id_unique IF NOT EXISTS
FOR (n:Topic)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT concept_id_unique IF NOT EXISTS
FOR (n:Concept)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT formula_id_unique IF NOT EXISTS
FOR (n:Formula)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT theorem_id_unique IF NOT EXISTS
FOR (n:Theorem)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT skill_id_unique IF NOT EXISTS
FOR (n:Skill)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT example_id_unique IF NOT EXISTS
FOR (n:Example)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT misconception_id_unique IF NOT EXISTS
FOR (n:Misconception)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT source_id_unique IF NOT EXISTS
FOR (n:Source)
REQUIRE n.id IS UNIQUE;
