# Bug修复记录模板

## 基本信息
- **修复日期**: YYYY-MM-DD
- **修复人员**: [修复者姓名/Claude]
- **Bug ID**: [如果有ticket系统的ID]
- **优先级**: Critical/High/Medium/Low
- **状态**: Fixed/Ongoing/Deferred

## Bug描述
### 问题标题
[简短描述问题]

### 详细描述
[详细描述bug现象、复现步骤、影响范围]

### 错误信息
```
[粘贴具体的错误信息或截图]
```

## 环境信息
- **前端/后端**: Frontend/Backend/Both
- **技术栈**: [Next.js, React, FastAPI等]
- **版本信息**: [相关依赖版本]
- **浏览器/运行环境**: [如果相关]

## 影响分析
### 涉及组件
- [组件1]: `frontend/src/components/xxx`
- [组件2]: `backend/services/xxx`

### 涉及函数
- [函数1]: `componentName.functionName()`
- [函数2]: `serviceName.methodName()`

### 相关文件
- `frontend/src/xxx.tsx`
- `backend/xxx.py`
- `config/xxx.json`

## 根本原因分析
### 问题根源
[分析bug产生的根本原因]

### 相关技术原理
[涉及的技术原理，便于理解和学习]

## 修复方案
### 解决思路
[解决问题的整体思路和策略]

### 具体实施步骤
1. **步骤1**: [具体操作]
   - 修改文件: `path/to/file`
   - 修改内容: [具体修改内容]
   - 原因: [为什么这样修改]

2. **步骤2**: [具体操作]
   - 修改文件: `path/to/file`
   - 修改内容: [具体修改内容]
   - 原因: [为什么这样修改]

### 代码变更
#### 修改前
```javascript/python/css
[修改前的代码]
```

#### 修改后
```javascript/python/css
[修改后的代码]
```

## 测试验证
### 测试方法
[如何验证修复效果]

### 测试结果
- ✅ [测试项目1]: 通过
- ✅ [测试项目2]: 通过
- ❌ [测试项目3]: 失败 (如果有)

## 影响评估
### 正面影响
- [修复后的改善]

### 潜在风险
- [可能的副作用或风险]

### 回归测试
- [需要进行的回归测试项目]

## 学习总结
### 技术收获
[从这次修复中学到的技术知识]

### 经验教训
[避免类似问题的经验]

### 最佳实践
[相关的最佳开发实践]

## 相关资源
### 参考文档
- [相关技术文档链接]
- [相关bug报告或讨论]

### 相关修复记录
- [相关的其他bug修复记录]

## 标签
```yaml
tags:
  type: [render/style/api/logic/perf/security/config/deploy]
  severity: [critical/high/medium/low]
  frontend: [true/false]
  backend: [true/false]
  frameworks: [NextJS, React, FastAPI, etc.]
  components: [component1, component2]
  files: [file1.tsx, file2.py]
  functions: [func1(), func2()]
```

---
**创建日期**: YYYY-MM-DD
**最后更新**: YYYY-MM-DD