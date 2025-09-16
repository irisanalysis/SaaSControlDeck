# SaaS Control Deck 数据库部署执行指南

## 🎯 执行环境选择

### ⭐ **推荐方案：云服务器执行**

**适用场景**:
- 生产环境数据库初始化
- 正式部署和配置
- 需要完整系统权限的操作

**优势**:
✅ 网络连接稳定，延迟低
✅ 完整的系统管理权限
✅ 可以安装PostgreSQL客户端工具
✅ 执行环境与数据库服务器在同一网络
✅ 安全性更高，避免远程操作风险

**执行步骤**:
```bash
# 1. 登录云服务器
ssh your_username@your_cloud_server

# 2. 克隆项目代码
git clone https://github.com/irisanalysis/SaaSControlDeck.git
cd SaaSControlDeck

# 3. 安装PostgreSQL客户端
sudo apt-get update
sudo apt-get install postgresql-client

# 4. 执行一键部署
./scripts/database/deploy-saascontrol-databases.sh

# 5. 验证部署结果
./scripts/database/deploy-saascontrol-databases.sh --test-only
```

---

### 🔧 **备选方案：Firebase Studio执行**

**适用场景**:
- 开发环境测试
- 快速验证配置
- 无法直接访问云服务器时

**限制和挑战**:
⚠️ Firebase Studio Nix环境可能缺少PostgreSQL客户端
⚠️ 网络连接可能不如云服务器稳定
⚠️ 权限限制，可能无法安装系统工具
⚠️ 安全性相对较低

**替代执行方案**:
```bash
# 在Firebase Studio终端中
# 由于环境限制，使用Python版本的部署脚本

# 1. 检查连接性
python3 scripts/database/test-db-connectivity.py

# 2. 使用Python执行SQL脚本（需要psycopg2）
# 注意：可能需要手动安装依赖
pip install psycopg2-binary

# 3. 创建Python版本的部署脚本
python3 scripts/database/deploy-via-python.py
```

---

## 🚀 推荐执行流程

### **阶段1: 云服务器执行（生产部署）**

```bash
# 在云服务器 (47.79.87.199) 或具有访问权限的服务器上执行

# 登录云服务器
ssh user@47.79.87.199

# 克隆最新代码
git clone https://github.com/irisanalysis/SaaSControlDeck.git
cd SaaSControlDeck

# 安装必要工具
sudo apt-get update && sudo apt-get install -y postgresql-client

# 执行数据库部署
chmod +x scripts/database/deploy-saascontrol-databases.sh
./scripts/database/deploy-saascontrol-databases.sh

# 验证部署成功
./scripts/database/deploy-saascontrol-databases.sh --test-only
```

### **阶段2: Firebase Studio配置（开发环境）**

```bash
# 在Firebase Studio终端中配置开发环境

# 1. 复制环境配置文件
cp .env.saascontrol-multi-environment .env

# 2. 配置开发数据库连接
export DATABASE_URL="postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1"

# 3. 测试连接
python3 scripts/database/test-db-connectivity.py

# 4. 启动后端服务（连接到外部数据库）
npm run dev
```

---

## 🔍 执行前检查清单

### **网络连接测试**
```bash
# 测试PostgreSQL服务器连接性
telnet 47.79.87.199 5432
# 或
nc -zv 47.79.87.199 5432
```

### **权限验证**
```bash
# 测试管理员账户连接
psql -h 47.79.87.199 -p 5432 -U jackchan -d postgres
```

### **系统依赖检查**
```bash
# 检查PostgreSQL客户端
which psql
psql --version

# 检查必要的系统工具
which git
which curl
```

---

## ⚡ 快速决策指南

**如果您有云服务器SSH访问权限** → 选择云服务器执行
**如果您只能使用Firebase Studio** → 使用Python替代方案
**如果您需要快速测试连接** → Firebase Studio + 连接验证脚本
**如果您要正式部署生产环境** → 必须使用云服务器执行

---

## 🚨 重要安全提醒

1. **生产环境操作**: 建议在云服务器上执行，确保网络安全
2. **权限隔离**: 使用专用数据库用户，避免使用超级用户权限
3. **备份策略**: 执行前确保现有数据已备份
4. **网络安全**: 确保PostgreSQL服务器防火墙配置正确
5. **密码安全**: 部署后立即更改默认密码

---

## 📞 故障排除

**连接失败**: 检查防火墙和网络配置
**权限错误**: 验证用户账户和密码
**工具缺失**: 安装postgresql-client包
**脚本执行失败**: 检查文件权限和shell环境

**技术支持**: 查看deployment日志文件获取详细错误信息