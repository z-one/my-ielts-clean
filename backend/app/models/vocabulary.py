from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class VocabularyWord(Base):
    __tablename__ = "vocabulary_words"
    __table_args__ = {"comment": "词库单词表"}

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True, comment="用户ID，空表示系统词")
    chapter_name = Column(String(100), nullable=False, index=True, comment="章节名称")
    group_name = Column(String(100), nullable=True, comment="分组名称")
    word = Column(Text, nullable=False, comment="主单词")
    word_variants = Column(Text, default="", comment="单词变体JSON数组")
    pos = Column(String(100), default="", comment="词性")
    meaning = Column(Text, default="", comment="中文释义")
    example = Column(Text, default="", comment="例句")
    extra = Column(Text, default="", comment="补充说明")
    metadata_json = Column("metadata", Text, default="", comment="导入来源和扩展元数据JSON")
    source = Column(String(20), nullable=False, default="system", index=True, comment="来源：system/custom")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), comment="更新时间")


class VocabularyChapter(Base):
    __tablename__ = "vocabulary_chapters"
    __table_args__ = (
        UniqueConstraint("source", "chapter_name", name="uq_vocabulary_chapters_source_chapter"),
        {"comment": "词库章节目录表"},
    )

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    chapter_name = Column(String(100), nullable=False, index=True, comment="章节名称")
    label = Column(String(100), nullable=False, comment="展示名称")
    audio = Column(String(255), default="", comment="章节音频文件名")
    source = Column(String(20), nullable=False, default="system", index=True, comment="来源：system/youdao/custom")
    group_count = Column(Integer, nullable=False, default=0, comment="分组数量")
    word_count = Column(Integer, nullable=False, default=0, comment="单词数量")
    sort_order = Column(Integer, nullable=False, default=0, index=True, comment="排序")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), comment="更新时间")
