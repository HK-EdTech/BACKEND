// Hong Kong S1-S6 mathematics knowledge graph.
// Knowledge relationships are primary; grade/topic relationships are metadata.

// Stages and grades
MERGE (junior:Stage {id: "stage-junior-secondary", name_zh: "初中", name_en: "Junior Secondary"})
MERGE (senior:Stage {id: "stage-senior-secondary", name_zh: "高中", name_en: "Senior Secondary"})

MERGE (s1:Grade {id: "grade-s1", name_zh: "中一", name_en: "Secondary 1"})
MERGE (s2:Grade {id: "grade-s2", name_zh: "中二", name_en: "Secondary 2"})
MERGE (s3:Grade {id: "grade-s3", name_zh: "中三", name_en: "Secondary 3"})
MERGE (s4:Grade {id: "grade-s4", name_zh: "中四", name_en: "Secondary 4"})
MERGE (s5:Grade {id: "grade-s5", name_zh: "中五", name_en: "Secondary 5"})
MERGE (s6:Grade {id: "grade-s6", name_zh: "中六", name_en: "Secondary 6"})

MERGE (junior)-[:HAS_GRADE]->(s1)
MERGE (junior)-[:HAS_GRADE]->(s2)
MERGE (junior)-[:HAS_GRADE]->(s3)
MERGE (senior)-[:HAS_GRADE]->(s4)
MERGE (senior)-[:HAS_GRADE]->(s5)
MERGE (senior)-[:HAS_GRADE]->(s6)

MERGE (numberAlgebra:Strand {
  id: "strand-number-and-algebra",
  name_zh: "数与代数",
  name_en: "Number and Algebra"
})

MERGE (topic:Topic {
  id: "topic-s4-polynomial-factor-theorem",
  name_zh: "多项式与因式定理",
  name_en: "Polynomial and Factor Theorem"
})

MERGE (s4)-[:HAS_STRAND]->(numberAlgebra)
MERGE (numberAlgebra)-[:HAS_TOPIC]->(topic)

// Core concepts
MERGE (integer:Concept {
  id: "concept-integer",
  name_zh: "整数",
  name_en: "Integer",
  level: "foundation",
  definition_zh: "没有小数部分的正数、负数或零。",
  search_text: "整数 正数 负数 零 数学基础"
})

MERGE (fraction:Concept {
  id: "concept-fraction",
  name_zh: "分数",
  name_en: "Fraction",
  level: "foundation",
  definition_zh: "表示两个整数之比的数。",
  search_text: "分数 分子 分母 有理数 数学基础"
})

MERGE (substitution:Concept {
  id: "concept-algebraic-substitution",
  name_zh: "代数式代入求值",
  name_en: "Algebraic Substitution",
  level: "foundation",
  definition_zh: "将变量的指定数值代入代数式并计算结果。",
  search_text: "代入求值 代数式 变量 数值"
})

MERGE (algebraicExpression:Concept {
  id: "concept-algebraic-expression",
  name_zh: "代数式",
  name_en: "Algebraic Expression",
  level: "foundation",
  definition_zh: "由常数、变量和运算符号组成的数学表达式。",
  search_text: "代数式 变量 常数 项 系数"
})

MERGE (polynomial:Concept {
  id: "concept-polynomial",
  name_zh: "多项式",
  name_en: "Polynomial",
  level: "intermediate",
  definition_zh: "由一个或多个代数项组成的代数式。",
  search_text: "多项式 项 系数 常数项 次数 代数式"
})

MERGE (polynomialEvaluation:Concept {
  id: "concept-polynomial-evaluation",
  name_zh: "多项式代入求值",
  name_en: "Polynomial Evaluation",
  level: "intermediate",
  definition_zh: "将指定数值代入多项式并计算其值。",
  search_text: "多项式 代入求值 P(a) 变量"
})

MERGE (factorisation:Concept {
  id: "concept-factorisation",
  name_zh: "因式分解",
  name_en: "Factorisation",
  level: "intermediate",
  definition_zh: "将多项式表示为两个或多个多项式乘积的过程。",
  search_text: "因式分解 多项式 乘积 公因式 恒等式"
})

MERGE (factor:Concept {
  id: "concept-factor",
  name_zh: "因式",
  name_en: "Factor",
  level: "intermediate",
  definition_zh: "能够整除另一个代数式的代数式。",
  search_text: "因式 整除 多项式"
})

MERGE (root:Concept {
  id: "concept-polynomial-root",
  name_zh: "多项式的根",
  name_en: "Polynomial Root",
  level: "intermediate",
  definition_zh: "使多项式 P(x) 等于零的变量值。",
  search_text: "多项式的根 P(x)=0 方程解"
})

MERGE (polynomialEquation:Concept {
  id: "concept-polynomial-equation",
  name_zh: "多项式方程",
  name_en: "Polynomial Equation",
  level: "intermediate",
  definition_zh: "含有多项式的方程。",
  search_text: "多项式方程 方程 根 解 因式分解"
})

MERGE (remainder:Concept {
  id: "concept-polynomial-remainder",
  name_zh: "多项式除法的余式",
  name_en: "Polynomial Remainder",
  level: "intermediate",
  definition_zh: "多项式除法中次数低于除式的剩余部分。",
  search_text: "多项式除法 余式 商 被除式 除式"
})

// Theorems and formulas
MERGE (factorTheorem:Theorem {
  id: "theorem-factor-theorem",
  name_zh: "因式定理",
  name_en: "Factor Theorem",
  statement_zh: "若 P(a)=0，则 x-a 是 P(x) 的因式；反之亦然。",
  search_text: "因式定理 P(a)=0 x-a 因式 根"
})

MERGE (remainderTheorem:Theorem {
  id: "theorem-remainder-theorem",
  name_zh: "余式定理",
  name_en: "Remainder Theorem",
  statement_zh: "多项式 P(x) 除以 x-a 所得的余式为 P(a)。",
  search_text: "余式定理 P(a) 多项式除法 x-a 余式"
})

MERGE (factorFormula:Formula {
  id: "formula-factor-theorem",
  expression: "P(a) = 0",
  meaning_zh: "x-a 是 P(x) 的因式"
})

MERGE (remainderFormula:Formula {
  id: "formula-remainder-theorem",
  expression: "Remainder = P(a)",
  meaning_zh: "P(x) 除以 x-a 的余式等于 P(a)"
})

// Skills, examples, misconception, and source
MERGE (evaluateSkill:Skill {
  id: "skill-evaluate-polynomial",
  name_zh: "计算多项式的值",
  name_en: "Evaluate a Polynomial",
  search_text: "代入 多项式 求值 P(a)"
})

MERGE (factoriseSkill:Skill {
  id: "skill-factorise-polynomial",
  name_zh: "进行多项式因式分解",
  name_en: "Factorise a Polynomial",
  search_text: "因式分解 多项式 公因式 恒等式"
})

MERGE (identifyFactorSkill:Skill {
  id: "skill-identify-factor",
  name_zh: "判断一次式是否为因式",
  name_en: "Identify Whether a Linear Expression Is a Factor",
  search_text: "因式定理 判断因式 P(a)=0"
})

MERGE (factorExample:Example {
  id: "example-factor-theorem-001",
  name_zh: "判断 x-2 是否为因式",
  question_zh: "判断 x-2 是否为 P(x)=x^3-2x+1 的因式。",
  answer_zh: "不是因式，因为 P(2)=5，不等于 0。",
  search_text: "因式定理 例题 x-2 P(x)=x^3-2x+1"
})

MERGE (remainderExample:Example {
  id: "example-remainder-theorem-001",
  name_zh: "利用余式定理求余式",
  question_zh: "求 P(x)=x^3-2x+1 除以 x-2 的余式。",
  answer_zh: "余式为 P(2)=5。",
  search_text: "余式定理 例题 多项式除法 余式"
})

MERGE (signMisconception:Misconception {
  id: "misconception-factor-theorem-sign",
  description_zh: "把 x-a 错误地代入为 P(-a)，或混淆 x-a 与 x+a。",
  correction_zh: "对于 x-a，应计算 P(a)；对于 x+a，应计算 P(-a)。",
  search_text: "因式定理 符号错误 P(a) P(-a) x-a x+a"
})

MERGE (source:Source {
  id: "source-hkedtech-polynomial-demo",
  title_zh: "香港中四多项式与因式定理知识图谱示例",
  source_type: "project-data",
  reliability: "internal-review"
})

// Curriculum metadata
MERGE (topic)-[:TEACHES]->(polynomial)
MERGE (topic)-[:TEACHES]->(factorisation)
MERGE (topic)-[:TEACHES]->(factorTheorem)
MERGE (topic)-[:TEACHES]->(remainderTheorem)
MERGE (polynomial)-[:APPEARS_IN]->(topic)
MERGE (factorisation)-[:APPEARS_IN]->(topic)
MERGE (factorTheorem)-[:APPEARS_IN]->(topic)
MERGE (remainderTheorem)-[:APPEARS_IN]->(topic)

// Knowledge relationships: prerequisite -> later knowledge
MERGE (integer)-[:PREREQUISITE_OF {strength: 0.60, reason_zh: "整数是数与代数的基础。"}]->(fraction)
MERGE (fraction)-[:PREREQUISITE_OF {strength: 0.60, reason_zh: "分数运算是代数运算的基础之一。"}]->(algebraicExpression)
MERGE (algebraicExpression)-[:PREREQUISITE_OF {strength: 0.85, reason_zh: "学习多项式前需要理解代数式、变量和项。"}]->(polynomial)
MERGE (substitution)-[:PREREQUISITE_OF {strength: 0.90, reason_zh: "定理应用需要进行代入求值。"}]->(polynomialEvaluation)
MERGE (polynomial)-[:PREREQUISITE_OF {strength: 0.95, reason_zh: "因式定理和余式定理应用于多项式。"}]->(polynomialEvaluation)
MERGE (polynomialEvaluation)-[:PREREQUISITE_OF {strength: 0.95, reason_zh: "因式定理需要先计算 P(a)。"}]->(factorTheorem)
MERGE (factorisation)-[:PREREQUISITE_OF {strength: 0.75, reason_zh: "因式分解与因式定理互相支持。"}]->(factorTheorem)
MERGE (factor)-[:PREREQUISITE_OF {strength: 0.85, reason_zh: "理解因式是使用因式定理的基础。"}]->(factorTheorem)
MERGE (polynomial)-[:PREREQUISITE_OF {strength: 0.90, reason_zh: "余式定理应用于多项式。"}]->(remainderTheorem)
MERGE (factorTheorem)-[:PREREQUISITE_OF {strength: 0.90, reason_zh: "因式定理可以帮助找出多项式方程的根。"}]->(polynomialEquation)

// Theorem, formula, skill, example, misconception, and source links
MERGE (factorTheorem)-[:USES_FORMULA]->(factorFormula)
MERGE (remainderTheorem)-[:USES_FORMULA]->(remainderFormula)
MERGE (factorTheorem)-[:EXPLAINS]->(factor)
MERGE (factorTheorem)-[:IDENTIFIES]->(root)
MERGE (remainderTheorem)-[:EXPLAINS]->(remainder)
MERGE (factorTheorem)-[:SUPPORTS]->(factorisation)
MERGE (factorTheorem)-[:HELPS_SOLVE]->(polynomialEquation)
MERGE (factorisation)-[:HELPS_SOLVE]->(polynomialEquation)
MERGE (evaluateSkill)-[:APPLIES_CONCEPT]->(polynomialEvaluation)
MERGE (factoriseSkill)-[:APPLIES_CONCEPT]->(factorisation)
MERGE (identifyFactorSkill)-[:APPLIES_THEOREM]->(factorTheorem)
MERGE (factorTheorem)-[:HAS_EXAMPLE]->(factorExample)
MERGE (remainderTheorem)-[:HAS_EXAMPLE]->(remainderExample)
MERGE (factorExample)-[:DEMONSTRATES]->(factorTheorem)
MERGE (remainderExample)-[:DEMONSTRATES]->(remainderTheorem)
MERGE (factorTheorem)-[:HAS_MISCONCEPTION]->(signMisconception)
MERGE (polynomial)-[:SUPPORTED_BY]->(source)
MERGE (factorTheorem)-[:SUPPORTED_BY]->(source)
MERGE (remainderTheorem)-[:SUPPORTED_BY]->(source);
