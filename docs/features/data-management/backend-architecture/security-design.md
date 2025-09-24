# 数据管理功能 - 安全设计文档

## 🔒 安全架构概览

基于零信任安全模型，为数据管理功能设计多层次安全防护体系，涵盖身份验证、访问控制、数据保护、网络安全和合规性，确保用户数据的机密性、完整性和可用性。

## 🛡️ 安全设计原则

### 核心安全原则

```python
SECURITY_PRINCIPLES = {
    "zero_trust": "假设网络内外都不安全，验证每个请求",
    "defense_in_depth": "多层安全防护，单点失效不影响整体安全",
    "least_privilege": "最小权限原则，仅授予必要的访问权限",
    "data_minimization": "仅收集和处理必要的数据",
    "encryption_everywhere": "数据在传输和存储中均加密",
    "audit_everything": "记录所有安全相关的操作",
    "fail_secure": "系统故障时默认拒绝访问",
    "security_by_design": "安全性融入系统设计的每个环节"
}
```

### 威胁模型分析

```python
THREAT_MODEL = {
    # 外部威胁
    "external_threats": {
        "unauthorized_access": {
            "description": "未授权访问用户数据和系统资源",
            "impact": "HIGH",
            "mitigation": ["JWT认证", "多因素认证", "IP白名单"]
        },
        "data_breach": {
            "description": "敏感数据泄露或被窃取",
            "impact": "CRITICAL",
            "mitigation": ["端到端加密", "数据脱敏", "访问日志"]
        },
        "ddos_attacks": {
            "description": "分布式拒绝服务攻击",
            "impact": "MEDIUM",
            "mitigation": ["限流", "CDN防护", "负载均衡"]
        },
        "injection_attacks": {
            "description": "SQL注入、代码注入等攻击",
            "impact": "HIGH",
            "mitigation": ["参数化查询", "输入验证", "WAF防护"]
        }
    },

    # 内部威胁
    "internal_threats": {
        "privilege_escalation": {
            "description": "权限提升攻击",
            "impact": "HIGH",
            "mitigation": ["RBAC", "权限审计", "最小权限原则"]
        },
        "data_exfiltration": {
            "description": "内部人员数据窃取",
            "impact": "HIGH",
            "mitigation": ["数据分级", "访问控制", "行为监控"]
        },
        "system_misconfiguration": {
            "description": "系统配置错误导致的安全漏洞",
            "impact": "MEDIUM",
            "mitigation": ["配置审核", "自动化部署", "安全扫描"]
        }
    }
}
```

## 🔐 身份认证和授权

### JWT认证增强

```python
# JWT安全配置
JWT_CONFIG = {
    "algorithm": "ES256",  # 使用椭圆曲线签名算法
    "access_token_expire_minutes": 15,  # 访问令牌15分钟过期
    "refresh_token_expire_days": 7,     # 刷新令牌7天过期
    "issuer": "saascontrol-data-management",
    "audience": ["api", "websocket"],
    "key_rotation_days": 30,  # 密钥轮换周期

    # 增强安全特性
    "require_jti": True,      # 需要JWT ID防重放攻击
    "blacklist_enabled": True, # 启用令牌黑名单
    "rate_limit_enabled": True # 限制令牌签发频率
}

class EnhancedJWTAuth:
    def __init__(self):
        self.private_key = self.load_private_key()
        self.public_key = self.load_public_key()
        self.blacklist = RedisTokenBlacklist()

    async def create_access_token(self, user_data: dict) -> str:
        """创建安全的访问令牌"""
        now = datetime.utcnow()
        jti = str(uuid.uuid4())  # 唯一令牌ID

        payload = {
            "sub": user_data["user_id"],
            "email": user_data["email"],
            "role": user_data["role"],
            "permissions": user_data["permissions"],
            "iat": now,
            "exp": now + timedelta(minutes=JWT_CONFIG["access_token_expire_minutes"]),
            "iss": JWT_CONFIG["issuer"],
            "aud": JWT_CONFIG["audience"],
            "jti": jti,
            "device_fingerprint": await self.get_device_fingerprint(),
            "ip_address": await self.get_client_ip()
        }

        # 记录令牌签发日志
        await self.log_token_issuance(user_data["user_id"], jti)

        return jwt.encode(payload, self.private_key, algorithm=JWT_CONFIG["algorithm"])

    async def verify_token(self, token: str, request: Request) -> dict:
        """验证令牌的安全性"""
        try:
            # 1. 基础JWT验证
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[JWT_CONFIG["algorithm"]],
                audience=JWT_CONFIG["audience"],
                issuer=JWT_CONFIG["issuer"]
            )

            # 2. 检查令牌黑名单
            if await self.blacklist.is_blacklisted(payload["jti"]):
                raise SecurityError("Token has been revoked")

            # 3. 设备指纹验证
            current_fingerprint = await self.get_device_fingerprint()
            if payload.get("device_fingerprint") != current_fingerprint:
                await self.log_suspicious_activity(payload["sub"], "device_fingerprint_mismatch")
                raise SecurityError("Device fingerprint mismatch")

            # 4. IP地址验证
            current_ip = await self.get_client_ip()
            if payload.get("ip_address") != current_ip:
                # 记录IP变化但不拒绝（可能是合法的网络切换）
                await self.log_ip_change(payload["sub"], payload.get("ip_address"), current_ip)

            return payload

        except jwt.ExpiredSignatureError:
            raise SecurityError("Token has expired")
        except jwt.InvalidTokenError:
            raise SecurityError("Invalid token")

    async def revoke_token(self, jti: str, reason: str = "user_logout"):
        """撤销令牌"""
        await self.blacklist.add_token(jti, reason)
        await self.log_token_revocation(jti, reason)
```

### 多因素认证 (MFA)

```python
class MultiFactorAuth:
    def __init__(self):
        self.totp = pyotp.TOTP()
        self.sms_provider = SMSProvider()
        self.email_provider = EmailProvider()

    async def setup_mfa(self, user_id: str, method: str) -> dict:
        """设置多因素认证"""
        if method == "totp":
            return await self.setup_totp_mfa(user_id)
        elif method == "sms":
            return await self.setup_sms_mfa(user_id)
        elif method == "email":
            return await self.setup_email_mfa(user_id)

    async def setup_totp_mfa(self, user_id: str) -> dict:
        """设置TOTP认证"""
        # 生成密钥
        secret = pyotp.random_base32()

        # 生成QR码
        totp = pyotp.TOTP(secret)
        qr_code_url = totp.provisioning_uri(
            name=user_id,
            issuer_name="SaaSControl Data Management"
        )

        # 存储密钥（加密）
        await self.store_mfa_secret(user_id, "totp", secret)

        return {
            "method": "totp",
            "secret": secret,
            "qr_code_url": qr_code_url,
            "backup_codes": await self.generate_backup_codes(user_id)
        }

    async def verify_mfa_code(self, user_id: str, code: str, method: str) -> bool:
        """验证MFA代码"""
        user_mfa = await self.get_user_mfa_config(user_id)

        if method == "totp":
            secret = await self.decrypt_mfa_secret(user_mfa["secret"])
            totp = pyotp.TOTP(secret)

            # 验证代码（允许时间窗口误差）
            return totp.verify(code, valid_window=1)

        elif method == "sms" or method == "email":
            # 验证一次性代码
            return await self.verify_otp_code(user_id, code, method)

    async def generate_backup_codes(self, user_id: str) -> List[str]:
        """生成备用恢复代码"""
        backup_codes = []
        for _ in range(10):
            code = secrets.token_hex(8).upper()
            backup_codes.append(code)

        # 加密存储备用代码
        encrypted_codes = await self.encrypt_backup_codes(backup_codes)
        await self.store_backup_codes(user_id, encrypted_codes)

        return backup_codes
```

### 基于角色的访问控制 (RBAC)

```python
# RBAC权限模型
RBAC_MODEL = {
    "roles": {
        "admin": {
            "description": "系统管理员",
            "permissions": ["*"]  # 所有权限
        },
        "data_analyst": {
            "description": "数据分析师",
            "permissions": [
                "data_sources:read",
                "data_sources:create",
                "data_sources:update",
                "quality_analysis:read",
                "quality_analysis:create",
                "ai_chat:read",
                "ai_chat:create",
                "reports:read",
                "reports:create"
            ]
        },
        "viewer": {
            "description": "只读用户",
            "permissions": [
                "data_sources:read",
                "quality_analysis:read",
                "reports:read"
            ]
        },
        "guest": {
            "description": "访客用户",
            "permissions": [
                "data_sources:read:own",  # 只能查看自己的数据源
                "quality_analysis:read:own"
            ]
        }
    },

    "resources": {
        "data_sources": ["create", "read", "update", "delete", "share"],
        "quality_analysis": ["create", "read", "update", "delete"],
        "ai_chat": ["create", "read", "delete"],
        "reports": ["create", "read", "export"],
        "users": ["create", "read", "update", "delete"],
        "system": ["config", "monitor", "audit"]
    }
}

class RBACManager:
    async def check_permission(self, user_id: str, resource: str, action: str, resource_id: str = None) -> bool:
        """检查用户权限"""
        user_roles = await self.get_user_roles(user_id)
        user_permissions = await self.get_user_permissions(user_roles)

        # 检查通配符权限
        if "*" in user_permissions:
            return True

        # 检查具体权限
        permission = f"{resource}:{action}"
        if permission in user_permissions:
            return True

        # 检查资源级权限
        if resource_id:
            resource_permission = f"{resource}:{action}:own"
            if resource_permission in user_permissions:
                return await self.is_resource_owner(user_id, resource, resource_id)

        # 检查共享权限
        if resource_id and action == "read":
            return await self.has_shared_access(user_id, resource, resource_id)

        return False

    async def is_resource_owner(self, user_id: str, resource: str, resource_id: str) -> bool:
        """检查用户是否是资源所有者"""
        if resource == "data_sources":
            data_source = await self.db.get_data_source(resource_id)
            return data_source and data_source.user_id == user_id

        elif resource == "quality_analysis":
            analysis = await self.db.get_quality_assessment(resource_id)
            return analysis and analysis.user_id == user_id

        return False

    async def has_shared_access(self, user_id: str, resource: str, resource_id: str) -> bool:
        """检查用户是否有共享访问权限"""
        if resource == "data_sources":
            sharing = await self.db.get_data_sharing_permission(resource_id, user_id)
            return sharing and sharing.is_active and (
                sharing.expires_at is None or sharing.expires_at > datetime.utcnow()
            )

        return False
```

## 🔐 数据保护和加密

### 数据分级和标记

```python
# 数据分级策略
DATA_CLASSIFICATION = {
    "public": {
        "level": 0,
        "description": "公开数据，无保护要求",
        "encryption": False,
        "access_logging": False,
        "retention_days": 365
    },
    "internal": {
        "level": 1,
        "description": "内部数据，基础保护",
        "encryption": True,
        "access_logging": True,
        "retention_days": 1095  # 3年
    },
    "confidential": {
        "level": 2,
        "description": "机密数据，高级保护",
        "encryption": True,
        "access_logging": True,
        "masking_required": True,
        "retention_days": 2555  # 7年
    },
    "restricted": {
        "level": 3,
        "description": "受限数据，最高级保护",
        "encryption": True,
        "access_logging": True,
        "masking_required": True,
        "approval_required": True,
        "retention_days": 3650  # 10年
    }
}

class DataClassifier:
    async def classify_data_source(self, data_source_id: str) -> str:
        """自动分类数据源"""
        data_source = await self.get_data_source(data_source_id)
        data_sample = await self.get_data_sample(data_source_id, limit=100)

        # 使用规则引擎和AI模型进行分类
        classification_score = await self.analyze_data_sensitivity(data_sample)

        if classification_score >= 0.8:
            return "restricted"
        elif classification_score >= 0.6:
            return "confidential"
        elif classification_score >= 0.3:
            return "internal"
        else:
            return "public"

    async def analyze_data_sensitivity(self, data_sample: list) -> float:
        """分析数据敏感性"""
        sensitivity_indicators = {
            "personal_info": 0.4,      # 个人信息
            "financial_data": 0.5,     # 财务数据
            "health_data": 0.6,        # 健康数据
            "biometric_data": 0.8,     # 生物识别数据
            "government_id": 0.7       # 政府身份证件
        }

        max_sensitivity = 0.0
        for row in data_sample:
            for field, value in row.items():
                sensitivity = await self.detect_sensitive_field(field, str(value))
                max_sensitivity = max(max_sensitivity, sensitivity)

        return max_sensitivity
```

### 端到端加密

```python
class DataEncryption:
    def __init__(self):
        self.master_key = self.load_master_key()
        self.key_derivation = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.get_salt(),
            iterations=100000
        )

    async def encrypt_data_source(self, data_source_id: str, data: bytes) -> dict:
        """加密数据源"""
        # 1. 生成数据加密密钥 (DEK)
        dek = Fernet.generate_key()

        # 2. 使用DEK加密数据
        fernet = Fernet(dek)
        encrypted_data = fernet.encrypt(data)

        # 3. 使用主密钥加密DEK (信封加密)
        encrypted_dek = await self.encrypt_with_master_key(dek)

        # 4. 存储加密信息
        encryption_metadata = {
            "data_source_id": data_source_id,
            "encrypted_dek": encrypted_dek,
            "encryption_algorithm": "AES-256-GCM",
            "key_version": await self.get_current_key_version(),
            "encrypted_at": datetime.utcnow().isoformat()
        }

        await self.store_encryption_metadata(data_source_id, encryption_metadata)

        return {
            "encrypted_data": encrypted_data,
            "encryption_metadata": encryption_metadata
        }

    async def decrypt_data_source(self, data_source_id: str, encrypted_data: bytes) -> bytes:
        """解密数据源"""
        # 1. 获取加密元数据
        encryption_metadata = await self.get_encryption_metadata(data_source_id)

        # 2. 解密DEK
        encrypted_dek = encryption_metadata["encrypted_dek"]
        dek = await self.decrypt_with_master_key(encrypted_dek)

        # 3. 使用DEK解密数据
        fernet = Fernet(dek)
        decrypted_data = fernet.decrypt(encrypted_data)

        # 4. 记录解密操作
        await self.log_decryption_access(data_source_id)

        return decrypted_data

    async def rotate_encryption_keys(self):
        """密钥轮换"""
        # 1. 生成新的主密钥
        new_master_key = self.generate_new_master_key()

        # 2. 重新加密所有DEK
        encrypted_deks = await self.get_all_encrypted_deks()

        for data_source_id, old_encrypted_dek in encrypted_deks.items():
            # 用旧密钥解密DEK
            dek = await self.decrypt_with_old_master_key(old_encrypted_dek)

            # 用新密钥重新加密DEK
            new_encrypted_dek = await self.encrypt_with_new_master_key(dek)

            # 更新存储
            await self.update_encrypted_dek(data_source_id, new_encrypted_dek)

        # 3. 启用新密钥
        await self.activate_new_master_key(new_master_key)
```

### 数据脱敏

```python
class DataMasking:
    def __init__(self):
        self.masking_rules = {
            "email": self.mask_email,
            "phone": self.mask_phone,
            "ssn": self.mask_ssn,
            "credit_card": self.mask_credit_card,
            "name": self.mask_name,
            "address": self.mask_address
        }

    async def mask_sensitive_data(self, data: dict, classification: str) -> dict:
        """根据分类对敏感数据进行脱敏"""
        if classification not in ["confidential", "restricted"]:
            return data

        masked_data = {}
        for field, value in data.items():
            field_type = await self.detect_field_type(field, value)

            if field_type in self.masking_rules:
                masked_data[field] = self.masking_rules[field_type](value)
            else:
                masked_data[field] = value

        return masked_data

    def mask_email(self, email: str) -> str:
        """邮箱脱敏"""
        if "@" not in email:
            return email

        local, domain = email.split("@", 1)
        if len(local) <= 2:
            masked_local = "*" * len(local)
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

        return f"{masked_local}@{domain}"

    def mask_phone(self, phone: str) -> str:
        """手机号脱敏"""
        phone_digits = "".join(filter(str.isdigit, phone))
        if len(phone_digits) >= 7:
            return phone_digits[:3] + "*" * (len(phone_digits) - 6) + phone_digits[-3:]
        return "*" * len(phone)

    def mask_name(self, name: str) -> str:
        """姓名脱敏"""
        if len(name) <= 1:
            return "*" * len(name)
        elif len(name) == 2:
            return name[0] + "*"
        else:
            return name[0] + "*" * (len(name) - 2) + name[-1]

    async def create_anonymized_dataset(self, data_source_id: str) -> str:
        """创建匿名化数据集"""
        original_data = await self.get_data_source_data(data_source_id)

        # K-匿名化处理
        anonymized_data = await self.k_anonymize(original_data, k=5)

        # 差分隐私处理
        private_data = await self.apply_differential_privacy(anonymized_data)

        # 存储匿名化数据集
        anon_data_source_id = await self.store_anonymized_dataset(
            data_source_id, private_data
        )

        return anon_data_source_id
```

## 🔍 安全监控和审计

### 安全事件监控

```python
class SecurityMonitor:
    def __init__(self):
        self.event_rules = self.load_security_rules()
        self.ml_model = self.load_anomaly_detection_model()

    async def monitor_user_activity(self, user_id: str, activity: dict):
        """监控用户活动"""
        # 1. 基础安全检查
        await self.check_basic_security_rules(user_id, activity)

        # 2. 异常行为检测
        await self.detect_anomalous_behavior(user_id, activity)

        # 3. 威胁情报匹配
        await self.check_threat_intelligence(activity)

        # 4. 记录安全事件
        await self.log_security_event(user_id, activity)

    async def check_basic_security_rules(self, user_id: str, activity: dict):
        """基础安全规则检查"""
        # 检查可疑登录
        if activity["type"] == "login":
            await self.check_suspicious_login(user_id, activity)

        # 检查大量数据访问
        elif activity["type"] == "data_access":
            await self.check_bulk_data_access(user_id, activity)

        # 检查异常时间访问
        elif activity["type"] == "api_request":
            await self.check_off_hours_access(user_id, activity)

    async def detect_anomalous_behavior(self, user_id: str, activity: dict):
        """AI驱动的异常行为检测"""
        # 获取用户历史行为模式
        user_profile = await self.get_user_behavior_profile(user_id)

        # 计算当前活动的异常分数
        anomaly_score = await self.ml_model.predict_anomaly(
            user_profile, activity
        )

        if anomaly_score > 0.8:  # 高异常分数
            await self.raise_security_alert(
                user_id,
                "anomalous_behavior",
                {
                    "activity": activity,
                    "anomaly_score": anomaly_score,
                    "severity": "high"
                }
            )

    async def check_threat_intelligence(self, activity: dict):
        """威胁情报检查"""
        client_ip = activity.get("client_ip")
        user_agent = activity.get("user_agent")

        # 检查恶意IP
        if client_ip:
            is_malicious_ip = await self.threat_intel.check_ip_reputation(client_ip)
            if is_malicious_ip:
                await self.block_ip_address(client_ip)

        # 检查恶意User-Agent
        if user_agent:
            is_malicious_ua = await self.threat_intel.check_user_agent(user_agent)
            if is_malicious_ua:
                await self.flag_suspicious_user_agent(user_agent)

class SecurityAuditLogger:
    async def log_security_event(self, event_type: str, details: dict):
        """记录安全事件"""
        security_event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": details.get("user_id"),
            "resource": details.get("resource"),
            "action": details.get("action"),
            "result": details.get("result"),
            "client_ip": details.get("client_ip"),
            "user_agent": details.get("user_agent"),
            "severity": details.get("severity", "info"),
            "additional_data": details.get("additional_data", {})
        }

        # 存储到安全日志数据库
        await self.store_security_event(security_event)

        # 实时告警
        if security_event["severity"] in ["high", "critical"]:
            await self.send_security_alert(security_event)

    async def generate_audit_report(self, user_id: str, date_range: dict) -> dict:
        """生成用户审计报告"""
        events = await self.get_user_security_events(user_id, date_range)

        report = {
            "user_id": user_id,
            "reporting_period": date_range,
            "total_events": len(events),
            "event_summary": self.summarize_events(events),
            "risk_assessment": await self.assess_user_risk(events),
            "recommendations": await self.generate_security_recommendations(events)
        }

        return report
```

### 实时威胁检测

```python
class ThreatDetectionEngine:
    def __init__(self):
        self.detection_rules = self.load_detection_rules()
        self.ml_models = self.load_ml_models()

    async def real_time_threat_detection(self, event: dict):
        """实时威胁检测"""
        # 1. 规则引擎检测
        rule_matches = await self.apply_detection_rules(event)

        # 2. 机器学习检测
        ml_predictions = await self.apply_ml_detection(event)

        # 3. 综合威胁评分
        threat_score = await self.calculate_threat_score(rule_matches, ml_predictions)

        # 4. 威胁响应
        if threat_score >= 0.8:
            await self.execute_threat_response(event, threat_score)

        return {
            "threat_detected": threat_score >= 0.5,
            "threat_score": threat_score,
            "rule_matches": rule_matches,
            "ml_predictions": ml_predictions
        }

    async def apply_detection_rules(self, event: dict) -> list:
        """应用检测规则"""
        matches = []

        # 暴力破解检测
        if event["type"] == "login_failed":
            failed_attempts = await self.count_recent_failed_logins(
                event["user_id"], minutes=10
            )
            if failed_attempts >= 5:
                matches.append({
                    "rule": "brute_force_detection",
                    "severity": "high",
                    "description": f"{failed_attempts} failed login attempts in 10 minutes"
                })

        # 异常数据访问检测
        elif event["type"] == "data_access":
            if event["data_size"] > 100 * 1024 * 1024:  # 100MB
                matches.append({
                    "rule": "large_data_access",
                    "severity": "medium",
                    "description": f"Large data access: {event['data_size']} bytes"
                })

        # 权限提升检测
        elif event["type"] == "permission_change":
            if event["new_role"] == "admin":
                matches.append({
                    "rule": "privilege_escalation",
                    "severity": "critical",
                    "description": "User role changed to admin"
                })

        return matches

    async def execute_threat_response(self, event: dict, threat_score: float):
        """执行威胁响应"""
        if threat_score >= 0.9:
            # 严重威胁：立即阻断
            await self.block_user_session(event["user_id"])
            await self.notify_security_team("critical_threat", event)

        elif threat_score >= 0.7:
            # 高威胁：增强监控
            await self.enable_enhanced_monitoring(event["user_id"])
            await self.require_additional_authentication(event["user_id"])

        elif threat_score >= 0.5:
            # 中等威胁：记录并监控
            await self.flag_for_investigation(event)
            await self.increase_audit_logging(event["user_id"])
```

## 🌐 网络安全

### Web应用防火墙 (WAF)

```python
class WebApplicationFirewall:
    def __init__(self):
        self.attack_patterns = self.load_attack_patterns()
        self.rate_limiters = self.setup_rate_limiters()

    async def filter_request(self, request: Request) -> bool:
        """WAF请求过滤"""
        # 1. IP黑名单检查
        if await self.is_blacklisted_ip(request.client.host):
            await self.log_blocked_request(request, "blacklisted_ip")
            return False

        # 2. 攻击模式检测
        if await self.detect_attack_patterns(request):
            await self.log_blocked_request(request, "attack_pattern")
            return False

        # 3. 速率限制
        if not await self.check_rate_limits(request):
            await self.log_blocked_request(request, "rate_limit")
            return False

        # 4. 输入验证
        if not await self.validate_input(request):
            await self.log_blocked_request(request, "invalid_input")
            return False

        return True

    async def detect_attack_patterns(self, request: Request) -> bool:
        """检测攻击模式"""
        content = await self.extract_request_content(request)

        for pattern_name, pattern in self.attack_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                await self.log_attack_detection(request, pattern_name)
                return True

        return False

    async def check_rate_limits(self, request: Request) -> bool:
        """检查速率限制"""
        client_ip = request.client.host
        endpoint = request.url.path

        # 全局速率限制
        global_key = f"rate_limit:global:{client_ip}"
        if not await self.rate_limiters["global"].check_limit(global_key):
            return False

        # 端点特定速率限制
        endpoint_key = f"rate_limit:endpoint:{client_ip}:{endpoint}"
        if not await self.rate_limiters["endpoint"].check_limit(endpoint_key):
            return False

        return True

# 攻击模式定义
ATTACK_PATTERNS = {
    "sql_injection": r"(\b(union|select|insert|update|delete|drop|create|alter)\b|\b(or|and)\s+\d+\s*=\s*\d+|\b(exec|execute)\s*\(|\bsp_\w+|\bxp_\w+)",
    "xss": r"(<script[^>]*>.*?</script>|javascript:|on\w+\s*=|<iframe[^>]*>|<object[^>]*>)",
    "command_injection": r"(\b(cat|ls|pwd|id|uname|whoami|ps|netstat|ifconfig)\b|[;&|`$]|\.\./)",
    "path_traversal": r"(\.\./|\.\.\\\|%2e%2e%2f|%2e%2e\\)",
    "ldap_injection": r"(\*\)|\(\*|\)\s*\(\s*\||\|\s*\(\s*&)",
    "nosql_injection": r"(\{\s*\$\w+\s*:|\[\s*\$\w+\s*\])"
}
```

### DDoS防护

```python
class DDoSProtection:
    def __init__(self):
        self.connection_tracker = ConnectionTracker()
        self.adaptive_limiter = AdaptiveRateLimiter()

    async def check_ddos_protection(self, request: Request) -> bool:
        """DDoS防护检查"""
        client_ip = request.client.host

        # 1. 连接数检查
        if not await self.check_connection_limits(client_ip):
            return False

        # 2. 请求频率检查
        if not await self.check_request_frequency(client_ip):
            return False

        # 3. 带宽检查
        if not await self.check_bandwidth_limits(client_ip):
            return False

        # 4. 行为分析
        if await self.detect_bot_behavior(client_ip, request):
            return False

        return True

    async def check_connection_limits(self, client_ip: str) -> bool:
        """检查连接数限制"""
        current_connections = await self.connection_tracker.get_connection_count(client_ip)

        # 普通用户最多50个并发连接
        max_connections = 50

        if current_connections > max_connections:
            await self.log_ddos_attempt(client_ip, "too_many_connections")
            return False

        return True

    async def adaptive_rate_limiting(self, client_ip: str) -> bool:
        """自适应速率限制"""
        # 根据系统负载动态调整限制
        system_load = await self.get_system_load()

        if system_load > 0.8:
            # 高负载时更严格的限制
            max_requests = 10
        elif system_load > 0.6:
            # 中等负载时中等限制
            max_requests = 50
        else:
            # 低负载时宽松限制
            max_requests = 100

        return await self.adaptive_limiter.check_limit(
            client_ip, max_requests, window_seconds=60
        )

    async def detect_bot_behavior(self, client_ip: str, request: Request) -> bool:
        """检测机器人行为"""
        behavioral_signals = {
            "no_user_agent": not request.headers.get("user-agent"),
            "suspicious_user_agent": await self.is_suspicious_user_agent(
                request.headers.get("user-agent", "")
            ),
            "no_referer": not request.headers.get("referer"),
            "rapid_requests": await self.check_rapid_requests(client_ip),
            "unusual_patterns": await self.detect_unusual_access_patterns(client_ip)
        }

        # 如果多个信号表明是机器人行为
        bot_signals = sum(behavioral_signals.values())
        if bot_signals >= 3:
            await self.log_bot_detection(client_ip, behavioral_signals)
            return True

        return False
```

## 📋 合规性和隐私保护

### GDPR合规

```python
class GDPRCompliance:
    async def handle_data_subject_request(self, request_type: str, user_id: str) -> dict:
        """处理数据主体权利请求"""
        if request_type == "access":
            return await self.handle_access_request(user_id)
        elif request_type == "rectification":
            return await self.handle_rectification_request(user_id)
        elif request_type == "erasure":
            return await self.handle_erasure_request(user_id)
        elif request_type == "portability":
            return await self.handle_portability_request(user_id)

    async def handle_access_request(self, user_id: str) -> dict:
        """处理访问请求 - 用户有权知道我们处理了哪些个人数据"""
        user_data = {
            "personal_info": await self.get_user_personal_info(user_id),
            "data_sources": await self.get_user_data_sources(user_id),
            "quality_assessments": await self.get_user_quality_assessments(user_id),
            "ai_chat_history": await self.get_user_ai_chat_history(user_id),
            "access_logs": await self.get_user_access_logs(user_id),
            "sharing_permissions": await self.get_user_sharing_permissions(user_id)
        }

        # 生成可读格式的数据报告
        report = await self.generate_data_subject_report(user_data)

        return {
            "request_type": "access",
            "user_id": user_id,
            "report": report,
            "generated_at": datetime.utcnow().isoformat()
        }

    async def handle_erasure_request(self, user_id: str) -> dict:
        """处理删除请求 - 被遗忘权"""
        # 1. 检查是否可以删除（法律要求保留的数据）
        retention_check = await self.check_legal_retention_requirements(user_id)

        if not retention_check["can_delete"]:
            return {
                "request_type": "erasure",
                "status": "partial",
                "reason": retention_check["reason"],
                "retained_data": retention_check["retained_categories"]
            }

        # 2. 执行数据删除
        deletion_results = await self.execute_data_deletion(user_id)

        # 3. 记录删除操作
        await self.log_erasure_operation(user_id, deletion_results)

        return {
            "request_type": "erasure",
            "status": "completed",
            "deleted_data": deletion_results,
            "completed_at": datetime.utcnow().isoformat()
        }

    async def ensure_consent_management(self, user_id: str, processing_purpose: str):
        """确保处理活动有适当的法律依据"""
        consent = await self.get_user_consent(user_id, processing_purpose)

        if not consent or not consent.is_valid():
            raise ConsentRequiredError(f"Valid consent required for {processing_purpose}")

        # 记录处理活动
        await self.log_processing_activity(user_id, processing_purpose, consent.id)
```

### 数据保留策略

```python
class DataRetentionManager:
    def __init__(self):
        self.retention_policies = {
            "user_account_data": {"days": 2555, "after_event": "account_deletion"},
            "quality_analysis_results": {"days": 1095, "after_event": "creation"},
            "ai_chat_history": {"days": 365, "after_event": "last_activity"},
            "access_logs": {"days": 2555, "after_event": "creation"},
            "security_audit_logs": {"days": 3650, "after_event": "creation"},
            "temporary_files": {"days": 7, "after_event": "creation"}
        }

    async def schedule_data_cleanup(self):
        """调度数据清理任务"""
        for data_type, policy in self.retention_policies.items():
            expired_data = await self.find_expired_data(data_type, policy)

            if expired_data:
                await self.schedule_cleanup_task(data_type, expired_data)

    async def find_expired_data(self, data_type: str, policy: dict) -> list:
        """查找过期数据"""
        retention_days = policy["days"]
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        if data_type == "quality_analysis_results":
            return await self.db.find_old_quality_assessments(cutoff_date)
        elif data_type == "ai_chat_history":
            return await self.db.find_old_chat_sessions(cutoff_date)
        elif data_type == "temporary_files":
            return await self.file_storage.find_old_temp_files(cutoff_date)

        return []

    async def execute_secure_deletion(self, data_type: str, data_ids: list):
        """执行安全删除"""
        for data_id in data_ids:
            # 1. 创建删除审计记录
            await self.create_deletion_audit_record(data_type, data_id)

            # 2. 执行删除
            if data_type == "quality_analysis_results":
                await self.securely_delete_quality_assessment(data_id)
            elif data_type == "ai_chat_history":
                await self.securely_delete_chat_session(data_id)

            # 3. 验证删除完成
            await self.verify_deletion_completed(data_type, data_id)

    async def securely_delete_quality_assessment(self, assessment_id: str):
        """安全删除质量评估数据"""
        # 1. 删除主记录
        await self.db.delete_quality_assessment(assessment_id)

        # 2. 删除相关的AI分析结果
        await self.db.delete_ai_analysis_results(assessment_id)

        # 3. 删除评分历史
        await self.db.delete_scoring_history(assessment_id)

        # 4. 清理缓存
        await self.redis.delete_pattern(f"*{assessment_id}*")

        # 5. 安全删除文件
        await self.file_storage.secure_delete_assessment_files(assessment_id)
```

这个安全设计文档为数据管理功能提供了全面的安全保障，确保系统在各种威胁面前都能保护用户数据的安全和隐私。