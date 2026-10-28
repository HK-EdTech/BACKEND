// Hong Kong S1-S3 mathematics foundation expansion.
// This file adds reusable knowledge nodes and concept-first prerequisite links.
// It assumes the base graph from seed-core-concepts.cypher has already been loaded.

// Foundation topics
MERGE (s1Topic:Topic {
  id: "topic-s1-number-and-arithmetic",
  name_zh: "中一数与运算基础",
  name_en: "S1 Number and Arithmetic Foundations"
})

MERGE (s2Topic:Topic {
  id: "topic-s2-ratio-and-algebra",
  name_zh: "中二比率与代数基础",
  name_en: "S2 Ratio and Algebra Foundations"
})

MERGE (s3Topic:Topic {
  id: "topic-s3-equations-and-coordinate-geometry",
  name_zh: "中三方程与坐标几何基础",
  name_en: "S3 Equations and Coordinate Geometry Foundations"
})

MERGE (numberAlgebra:Strand {
  id: "strand-number-and-algebra",
  name_zh: "数与代数",
  name_en: "Number and Algebra"
})

MERGE (spaceShape:Strand {
  id: "strand-space-and-shape",
  name_zh: "空间与形状",
  name_en: "Space and Shape"
})

MERGE (s1:Grade {id: "grade-s1"})
MERGE (s2:Grade {id: "grade-s2"})
MERGE (s3:Grade {id: "grade-s3"})

MERGE (s1)-[:HAS_STRAND]->(numberAlgebra)
MERGE (s2)-[:HAS_STRAND]->(numberAlgebra)
MERGE (s3)-[:HAS_STRAND]->(numberAlgebra)
MERGE (s3)-[:HAS_STRAND]->(spaceShape)
MERGE (numberAlgebra)-[:HAS_TOPIC]->(s1Topic)
MERGE (numberAlgebra)-[:HAS_TOPIC]->(s2Topic)
MERGE (numberAlgebra)-[:HAS_TOPIC]->(s3Topic)
MERGE (spaceShape)-[:HAS_TOPIC]->(s3Topic)

// S1 concepts
MERGE (negativeNumber:Concept {
  id: "concept-negative-number",
  name_zh: "负数",
  name_en: "Negative Number",
  level: "foundation",
  definition_zh: "小于零的数。",
  search_text: "负数 数轴 正数 零 相反数"
})

MERGE (rationalNumber:Concept {
  id: "concept-rational-number",
  name_zh: "有理数",
  name_en: "Rational Number",
  level: "foundation",
  definition_zh: "可以表示为两个整数之比的数，其中分母不为零。",
  search_text: "有理数 整数 分数 正数 负数"
})

MERGE (decimal:Concept {
  id: "concept-decimal",
  name_zh: "小数",
  name_en: "Decimal",
  level: "foundation",
  definition_zh: "以十进制位值表示的数。",
  search_text: "小数 位值 有限小数 无限循环小数"
})

MERGE (percentage:Concept {
  id: "concept-percentage",
  name_zh: "百分数",
  name_en: "Percentage",
  level: "foundation",
  definition_zh: "以百分之一为单位表示的数。",
  search_text: "百分数 百分比 分数 小数"
})

MERGE (ratio:Concept {
  id: "concept-ratio",
  name_zh: "比",
  name_en: "Ratio",
  level: "foundation",
  definition_zh: "比较两个同类量大小的关系。",
  search_text: "比 比值 比例 比较 数量关系"
})

MERGE (rate:Concept {
  id: "concept-rate",
  name_zh: "率",
  name_en: "Rate",
  level: "foundation",
  definition_zh: "两个不同单位量之间的比较关系。",
  search_text: "率 速率 单位率 比率 单位换算"
})

// S2 concepts
MERGE (index:Concept {
  id: "concept-index",
  name_zh: "指数",
  name_en: "Index",
  level: "foundation",
  definition_zh: "表示相同因数重复相乘次数的记号。",
  search_text: "指数 幂 底数 指数律"
})

MERGE (algebraicSimplification:Concept {
  id: "concept-algebraic-simplification",
  name_zh: "代数式化简",
  name_en: "Algebraic Simplification",
  level: "foundation",
  definition_zh: "利用运算法则和同类项把代数式化为较简形式。",
  search_text: "代数式 化简 同类项 展开 括号"
})

MERGE (linearInequality:Concept {
  id: "concept-linear-inequality",
  name_zh: "一元一次不等式",
  name_en: "Linear Inequality",
  level: "foundation",
  definition_zh: "含有未知数且未知数最高次数为一次的不等式。",
  search_text: "一元一次不等式 不等号 解集 数轴"
})

MERGE (directVariation:Concept {
  id: "concept-direct-variation",
  name_zh: "正变关系",
  name_en: "Direct Variation",
  level: "foundation",
  definition_zh: "两个变量的比保持不变的关系。",
  search_text: "正变关系 变量 比例 常数"
})

// S3 concepts
MERGE (linearEquation:Concept {
  id: "concept-linear-equation",
  name_zh: "一元一次方程",
  name_en: "Linear Equation",
  level: "foundation",
  definition_zh: "未知数最高次数为一次的方程。",
  search_text: "一元一次方程 方程 未知数 解"
})

MERGE (simultaneousEquations:Concept {
  id: "concept-simultaneous-linear-equations",
  name_zh: "联立方程",
  name_en: "Simultaneous Linear Equations",
  level: "foundation",
  definition_zh: "需要同时满足两个或多个方程的方程组。",
  search_text: "联立方程 方程组 代入法 消元法"
})

MERGE (coordinatePlane:Concept {
  id: "concept-coordinate-plane",
  name_zh: "直角坐标平面",
  name_en: "Coordinate Plane",
  level: "foundation",
  definition_zh: "由互相垂直的数轴组成，用有序对表示点的位置。",
  search_text: "坐标平面 横坐标 纵坐标 有序对 象限"
})

MERGE (linearGraph:Concept {
  id: "concept-linear-graph",
  name_zh: "直线图像",
  name_en: "Linear Graph",
  level: "foundation",
  definition_zh: "一次关系在坐标平面上的图像。",
  search_text: "直线图像 斜率 截距 y=mx+c 坐标"
})

MERGE (basicAngle:Concept {
  id: "concept-basic-angle-properties",
  name_zh: "基本角性质",
  name_en: "Basic Angle Properties",
  level: "foundation",
  definition_zh: "包括对顶角、邻补角及平行线角等基本角关系。",
  search_text: "角 对顶角 邻补角 平行线 同位角 内错角"
})

// Curriculum metadata
MERGE (s1Topic)-[:TEACHES]->(negativeNumber)
MERGE (s1Topic)-[:TEACHES]->(rationalNumber)
MERGE (s1Topic)-[:TEACHES]->(decimal)
MERGE (s1Topic)-[:TEACHES]->(percentage)
MERGE (s1Topic)-[:TEACHES]->(ratio)
MERGE (s1Topic)-[:TEACHES]->(rate)

MERGE (s2Topic)-[:TEACHES]->(index)
MERGE (s2Topic)-[:TEACHES]->(algebraicSimplification)
MERGE (s2Topic)-[:TEACHES]->(linearInequality)
MERGE (s2Topic)-[:TEACHES]->(directVariation)

MERGE (s3Topic)-[:TEACHES]->(linearEquation)
MERGE (s3Topic)-[:TEACHES]->(simultaneousEquations)
MERGE (s3Topic)-[:TEACHES]->(coordinatePlane)
MERGE (s3Topic)-[:TEACHES]->(linearGraph)
MERGE (s3Topic)-[:TEACHES]->(basicAngle)

MERGE (negativeNumber)-[:APPEARS_IN]->(s1Topic)
MERGE (rationalNumber)-[:APPEARS_IN]->(s1Topic)
MERGE (decimal)-[:APPEARS_IN]->(s1Topic)
MERGE (percentage)-[:APPEARS_IN]->(s1Topic)
MERGE (ratio)-[:APPEARS_IN]->(s1Topic)
MERGE (rate)-[:APPEARS_IN]->(s1Topic)
MERGE (index)-[:APPEARS_IN]->(s2Topic)
MERGE (algebraicSimplification)-[:APPEARS_IN]->(s2Topic)
MERGE (linearInequality)-[:APPEARS_IN]->(s2Topic)
MERGE (directVariation)-[:APPEARS_IN]->(s2Topic)
MERGE (linearEquation)-[:APPEARS_IN]->(s3Topic)
MERGE (simultaneousEquations)-[:APPEARS_IN]->(s3Topic)
MERGE (coordinatePlane)-[:APPEARS_IN]->(s3Topic)
MERGE (linearGraph)-[:APPEARS_IN]->(s3Topic)
MERGE (basicAngle)-[:APPEARS_IN]->(s3Topic)

// Reusable concept relationships
MERGE (integer)-[:PREREQUISITE_OF {strength: 0.85, reason_zh: "负数与整数共同构成有理数基础。"}]->(negativeNumber)
MERGE (integer)-[:PREREQUISITE_OF {strength: 0.90, reason_zh: "有理数可以由整数之比表示。"}]->(rationalNumber)
MERGE (negativeNumber)-[:PREREQUISITE_OF {strength: 0.80, reason_zh: "负数是理解有理数和数轴的基础。"}]->(rationalNumber)
MERGE (fraction)-[:PREREQUISITE_OF {strength: 0.85, reason_zh: "分数是有理数的一种表示。"}]->(rationalNumber)
MERGE (rationalNumber)-[:PREREQUISITE_OF {strength: 0.80, reason_zh: "有理数可用小数表示。"}]->(decimal)
MERGE (fraction)-[:PREREQUISITE_OF {strength: 0.80, reason_zh: "百分数可以转换为分数。"}]->(percentage)
MERGE (decimal)-[:PREREQUISITE_OF {strength: 0.80, reason_zh: "百分数可以转换为小数。"}]->(percentage)
MERGE (fraction)-[:PREREQUISITE_OF {strength: 0.75, reason_zh: "比常用分数表示两个量的关系。"}]->(ratio)
MERGE (ratio)-[:PREREQUISITE_OF {strength: 0.80, reason_zh: "率是具有单位背景的比。"}]->(rate)
MERGE (algebraicExpression)-[:PREREQUISITE_OF {strength: 0.85, reason_zh: "代数式化简需要理解变量、项和运算。"}]->(algebraicSimplification)
MERGE (index)-[:PREREQUISITE_OF {strength: 0.80, reason_zh: "指数用于表示幂和多项式中的次数。"}]->(polynomial)
MERGE (algebraicSimplification)-[:PREREQUISITE_OF {strength: 0.90, reason_zh: "化简代数式是处理方程和多项式的基础。"}]->(polynomial)
MERGE (algebraicSimplification)-[:PREREQUISITE_OF {strength: 0.85, reason_zh: "方程变形需要正确化简代数式。"}]->(linearEquation)
MERGE (linearEquation)-[:PREREQUISITE_OF {strength: 0.85, reason_zh: "联立方程扩展了一元一次方程的解法。"}]->(simultaneousEquations)
MERGE (coordinatePlane)-[:PREREQUISITE_OF {strength: 0.85, reason_zh: "直线图像建立在坐标平面上。"}]->(linearGraph)
MERGE (linearEquation)-[:RELATED_TO {reason_zh: "一次方程可以通过图像表示。"}]->(linearGraph)
MERGE (simultaneousEquations)-[:RELATED_TO {reason_zh: "联立方程可用两条直线的交点解释。"}]->(linearGraph)
MERGE (ratio)-[:PREREQUISITE_OF {strength: 0.70, reason_zh: "相似和比例问题经常使用比。"}]->(basicAngle)

// Shared concept relationships to the existing S4 graph
MERGE (linearEquation)-[:PREREQUISITE_OF {strength: 0.85, reason_zh: "方程的代数变形是学习多项式方程的基础。"}]->(polynomialEquation)
MERGE (algebraicSimplification)-[:PREREQUISITE_OF {strength: 0.85, reason_zh: "多项式运算需要代数式化简能力。"}]->(polynomial)

// Searchable learning context
SET negativeNumber.search_text = negativeNumber.search_text + " 中一 初中 数与代数"
SET rationalNumber.search_text = rationalNumber.search_text + " 中一 初中 数与代数"
SET algebraicSimplification.search_text = algebraicSimplification.search_text + " 中二 初中 数与代数"
SET linearEquation.search_text = linearEquation.search_text + " 中三 初中 数与代数"
SET linearGraph.search_text = linearGraph.search_text + " 中三 初中 坐标"
