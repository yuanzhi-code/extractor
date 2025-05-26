# Migration database schema with alembic

本项目使用 alembic 管理数据库schema

## 前提条件

- 同步依赖：

  ```bash
  uv sync
  ```


## 步骤 1：声明新的 ORM 模型

在 `src/models` 目录下创建一个新的 Python 文件（如 `src/models/user.py`）来定义 ORM 模型。以下是一个简单的用户模型示例：

```python
from sqlalchemy import Column, Integer, String
from src.models.db import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
```

### 说明

- 从 `src/models/base.py` 导入已声明的 `Base`。
- 模型类（如 `User`）继承自 `Base`，并定义表名和字段。
- 使用 `Column` 定义字段类型和约束（如 `primary_key`、`nullable`、`unique`）。

## 步骤 2：自动生成迁移脚本

1. 使用以下命令生成迁移脚本：

   ```bash
   alembic revision --autogenerate -m "<描述信息>"
   ```

   - `--autogenerate` 让 Alembic 检测模型变化，生成迁移脚本。
   - `-m` 指定迁移的描述信息。

2. 检查 `src/migrate/versions/` 目录中生成的新脚本，内容类似于：

   ```python
   from alembic import op
   import sqlalchemy as sa

   def upgrade():
       op.create_table(
           'users',
           sa.Column('id', sa.Integer(), nullable=False),
           sa.Column('name', sa.String(), nullable=False),
           sa.Column('email', sa.String(), nullable=False),
           sa.PrimaryKeyConstraint('id'),
           sa.UniqueConstraint('email')
       )

   def downgrade():
       op.drop_table('users')
   ```

## 步骤 3：应用迁移到数据库

1. 运行以下命令将迁移应用到 SQLite 数据库：

   ```bash
   alembic upgrade head
   ```

   - 这会执行所有未应用的迁移脚本，创建 `users` 表。

2. 验证数据库：
   - 检查项目根目录下的 `app.db` 文件。
   > 当前sqlite数据库的位置是写死的，这部分需要讨论一下

   - 使用你最喜欢的 SQLite 客户端（如 `sqlite3` 命令行工具）查看：

     ```bash
     sqlite3 example.db
     .tables
     ```

     输出应包含 `users` 表。

## 注意事项

- **模型变更**：如果修改了 `src/models`下的模型定义（如添加新字段），需要重新运行 `alembic revision --autogenerate -m "<desc>"`来生成新的 schema 版本 和 `alembic upgrade head` 将变更应用到数据库中。
- **错误排查**：提交前需要确认变更能确实的应用到你的数据库中。
- **备份**：在生产环境中，始终备份数据库后再应用迁移。
- **模块导入**：确保 `src/migrate/env.py` 中的导入路径正确，Python 能够找到 `src.models.db` 和 `src.models.user` 模块。
