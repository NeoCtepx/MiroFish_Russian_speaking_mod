"""
OASIS模拟管理器
管理Twitter和Reddit双平台并行模拟
使用预设脚本 + LLM智能生成配置参数
"""

import os
import json
import shutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.logger import get_logger
from .zep_entity_reader import ZepEntityReader, FilteredEntities
from .oasis_profile_generator import OasisProfileGenerator, OasisAgentProfile
from .simulation_config_generator import SimulationConfigGenerator, SimulationParameters
from ..utils.locale import t

logger = get_logger('mirofish.simulation')


class SimulationStatus(str, Enum):
    """模拟状态"""
    CREATED = "created"
    PREPARING = "preparing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"      # 模拟被手动停止
    COMPLETED = "completed"  # 模拟自然完成
    FAILED = "failed"


class PlatformType(str, Enum):
    """平台类型"""
    TWITTER = "twitter"
    REDDIT = "reddit"


@dataclass
class SimulationState:
    """模拟状态"""
    simulation_id: str
    project_id: str
    graph_id: str
    
    # 平台启用状态
    enable_twitter: bool = True
    enable_reddit: bool = True
    
    # 状态
    status: SimulationStatus = SimulationStatus.CREATED
    
    # 准备阶段数据
    entities_count: int = 0
    profiles_count: int = 0
    entity_types: List[str] = field(default_factory=list)
    
    # 配置生成信息
    config_generated: bool = False
    config_reasoning: str = ""
    
    # 运行时数据
    current_round: int = 0
    twitter_status: str = "not_started"
    reddit_status: str = "not_started"
    
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 错误信息
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """完整状态字典（内部使用）"""
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "enable_twitter": self.enable_twitter,
            "enable_reddit": self.enable_reddit,
            "status": self.status.value,
            "entities_count": self.entities_count,
            "profiles_count": self.profiles_count,
            "entity_types": self.entity_types,
            "config_generated": self.config_generated,
            "config_reasoning": self.config_reasoning,
            "current_round": self.current_round,
            "twitter_status": self.twitter_status,
            "reddit_status": self.reddit_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }
    
    def to_simple_dict(self) -> Dict[str, Any]:
        """简化状态字典（API返回使用）"""
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "status": self.status.value,
            "entities_count": self.entities_count,
            "profiles_count": self.profiles_count,
            "entity_types": self.entity_types,
            "config_generated": self.config_generated,
            "error": self.error,
        }


class SimulationManager:
    """
    模拟管理器
    
    核心功能：
    1. 从Zep图谱读取实体并过滤
    2. 生成OASIS Agent Profile
    3. 使用LLM智能生成模拟配置参数
    4. 准备预设脚本所需的所有文件
    """
    
    # 模拟数据存储目录
    SIMULATION_DATA_DIR = os.path.join(
        os.path.dirname(__file__), 
        '../../uploads/simulations'
    )
    
    def __init__(self):
        # 确保目录存在
        os.makedirs(self.SIMULATION_DATA_DIR, exist_ok=True)
        
        # 内存中的模拟状态缓存
        self._simulations: Dict[str, SimulationState] = {}
    
    def _get_simulation_dir(self, simulation_id: str) -> str:
        """获取模拟数据目录"""
        sim_dir = os.path.join(self.SIMULATION_DATA_DIR, simulation_id)
        os.makedirs(sim_dir, exist_ok=True)
        return sim_dir
    
    def _save_simulation_state(self, state: SimulationState):
        """保存模拟状态到文件"""
        sim_dir = self._get_simulation_dir(state.simulation_id)
        state_file = os.path.join(sim_dir, "state.json")
        
        state.updated_at = datetime.now().isoformat()
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        
        self._simulations[state.simulation_id] = state
    
    def _load_simulation_state(self, simulation_id: str) -> Optional[SimulationState]:
        """从文件加载模拟状态"""
        if simulation_id in self._simulations:
            return self._simulations[simulation_id]
        
        sim_dir = self._get_simulation_dir(simulation_id)
        state_file = os.path.join(sim_dir, "state.json")
        
        if not os.path.exists(state_file):
            return None
        
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        state = SimulationState(
            simulation_id=simulation_id,
            project_id=data.get("project_id", ""),
            graph_id=data.get("graph_id", ""),
            enable_twitter=data.get("enable_twitter", True),
            enable_reddit=data.get("enable_reddit", True),
            status=SimulationStatus(data.get("status", "created")),
            entities_count=data.get("entities_count", 0),
            profiles_count=data.get("profiles_count", 0),
            entity_types=data.get("entity_types", []),
            config_generated=data.get("config_generated", False),
            config_reasoning=data.get("config_reasoning", ""),
            current_round=data.get("current_round", 0),
            twitter_status=data.get("twitter_status", "not_started"),
            reddit_status=data.get("reddit_status", "not_started"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            error=data.get("error"),
        )
        
        self._simulations[simulation_id] = state
        return state
    
    def create_simulation(
        self,
        project_id: str,
        graph_id: str,
        enable_twitter: bool = True,
        enable_reddit: bool = True,
    ) -> SimulationState:
        """
        创建新的模拟
        
        Args:
            project_id: 项目ID
            graph_id: Zep图谱ID
            enable_twitter: 是否启用Twitter模拟
            enable_reddit: 是否启用Reddit模拟
            
        Returns:
            SimulationState
        """
        import uuid
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
        
        state = SimulationState(
            simulation_id=simulation_id,
            project_id=project_id,
            graph_id=graph_id,
            enable_twitter=enable_twitter,
            enable_reddit=enable_reddit,
            status=SimulationStatus.CREATED,
        )
        
        self._save_simulation_state(state)
        logger.info(f"创建模拟: {simulation_id}, project={project_id}, graph={graph_id}")
        
        return state
    
    def prepare_simulation(
        self,
        simulation_id: str,
        simulation_requirement: str,
        document_text: str,
        defined_entity_types: Optional[List[str]] = None,
        use_llm_for_profiles: bool = True,
        progress_callback: Optional[callable] = None,
        parallel_profile_count: int = 3
    ) -> SimulationState:
        """
        准备模拟环境（全程自动化）
        
        步骤：
        1. 从Zep图谱读取并过滤实体
        2. 为每个实体生成OASIS Agent Profile（可选LLM增强，支持并行）
        3. 使用LLM智能生成模拟配置参数（时间、活跃度、发言频率等）
        4. 保存配置文件和Profile文件
        5. 复制预设脚本到模拟目录
        
        Args:
            simulation_id: 模拟ID
            simulation_requirement: 模拟需求描述（用于LLM生成配置）
            document_text: 原始文档内容（用于LLM理解背景）
            defined_entity_types: 预定义的实体类型（可选）
            use_llm_for_profiles: 是否使用LLM生成详细人设
            progress_callback: 进度回调函数 (stage, progress, message)
            parallel_profile_count: 并行生成人设的数量，默认3
            
        Returns:
            SimulationState
        """
        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"模拟不存在: {simulation_id}")
        
        try:
            state.status = SimulationStatus.PREPARING
            self._save_simulation_state(state)
            
            sim_dir = self._get_simulation_dir(simulation_id)
            
            # ========== 阶段1: 读取并过滤实体 ==========
            if progress_callback:
                progress_callback("reading", 0, t('progress.connectingZepGraph'))
            
            reader = ZepEntityReader()
            
            if progress_callback:
                progress_callback("reading", 30, t('progress.readingNodeData'))
            
            filtered = reader.filter_defined_entities(
                graph_id=state.graph_id,
                defined_entity_types=defined_entity_types,
                enrich_with_edges=True
            )
            
            state.entities_count = filtered.filtered_count
            state.entity_types = list(filtered.entity_types)
            
            if progress_callback:
                progress_callback(
                    "reading", 100,
                    t('progress.readingComplete', count=filtered.filtered_count),
                    current=filtered.filtered_count,
                    total=filtered.filtered_count
                )
            
            if filtered.filtered_count == 0:
                state.status = SimulationStatus.FAILED
                state.error = "没有找到符合条件的实体，请检查图谱是否正确构建"
                self._save_simulation_state(state)
                return state
            
            # ========== 阶段2: 生成Agent Profile ==========
            total_entities = len(filtered.entities)
            
            if progress_callback:
                progress_callback(
                    "generating_profiles", 0,
                    t('progress.startGenerating'),
                    current=0,
                    total=total_entities
                )
            
            # 传入graph_id以启用Zep检索功能，获取更丰富的上下文
            generator = OasisProfileGenerator(graph_id=state.graph_id)
            
            def profile_progress(current, total, msg):
                if progress_callback:
                    progress_callback(
                        "generating_profiles", 
                        int(current / total * 100), 
                        msg,
                        current=current,
                        total=total,
                        item_name=msg
                    )
            
            # 设置实时保存的文件路径（优先使用 Reddit JSON 格式）
            realtime_output_path = None
            realtime_platform = "reddit"
            if state.enable_reddit:
                realtime_output_path = os.path.join(sim_dir, "reddit_profiles.json")
                realtime_platform = "reddit"
            elif state.enable_twitter:
                realtime_output_path = os.path.join(sim_dir, "twitter_profiles.csv")
                realtime_platform = "twitter"
            
            profiles = generator.generate_profiles_from_entities(
                entities=filtered.entities,
                use_llm=use_llm_for_profiles,
                progress_callback=profile_progress,
                graph_id=state.graph_id,  # 传入graph_id用于Zep检索
                parallel_count=parallel_profile_count,  # 并行生成数量
                realtime_output_path=realtime_output_path,  # 实时保存路径
                output_platform=realtime_platform  # 输出格式
            )
            
            state.profiles_count = len(profiles)
            
            # 保存Profile文件（注意：Twitter使用CSV格式，Reddit使用JSON格式）
            # Reddit 已经在生成过程中实时保存了，这里再保存一次确保完整性
            if progress_callback:
                progress_callback(
                    "generating_profiles", 95,
                    t('progress.savingProfiles'),
                    current=total_entities,
                    total=total_entities
                )
            
            if state.enable_reddit:
                generator.save_profiles(
                    profiles=profiles,
                    file_path=os.path.join(sim_dir, "reddit_profiles.json"),
                    platform="reddit"
                )
            
            if state.enable_twitter:
                # Twitter使用CSV格式！这是OASIS的要求
                generator.save_profiles(
                    profiles=profiles,
                    file_path=os.path.join(sim_dir, "twitter_profiles.csv"),
                    platform="twitter"
                )
            
            if progress_callback:
                progress_callback(
                    "generating_profiles", 100,
                    t('progress.profilesComplete', count=len(profiles)),
                    current=len(profiles),
                    total=len(profiles)
                )
            
            # ========== 阶段3: LLM智能生成模拟配置 ==========
            if progress_callback:
                progress_callback(
                    "generating_config", 0,
                    t('progress.analyzingRequirements'),
                    current=0,
                    total=3
                )
            
            config_generator = SimulationConfigGenerator()
            
            if progress_callback:
                progress_callback(
                    "generating_config", 30,
                    t('progress.callingLLMConfig'),
                    current=1,
                    total=3
                )
            
            sim_params = config_generator.generate_config(
                simulation_id=simulation_id,
                project_id=state.project_id,
                graph_id=state.graph_id,
                simulation_requirement=simulation_requirement,
                document_text=document_text,
                entities=filtered.entities,
                enable_twitter=state.enable_twitter,
                enable_reddit=state.enable_reddit
            )
            
            if progress_callback:
                progress_callback(
                    "generating_config", 70,
                    t('progress.savingConfigFiles'),
                    current=2,
                    total=3
                )
            
            # 保存配置文件
            config_path = os.path.join(sim_dir, "simulation_config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(sim_params.to_json())
            
            state.config_generated = True
            state.config_reasoning = sim_params.generation_reasoning
            
            if progress_callback:
                progress_callback(
                    "generating_config", 100,
                    t('progress.configComplete'),
                    current=3,
                    total=3
                )
            
            # 注意：运行脚本保留在 backend/scripts/ 目录，不再复制到模拟目录
            # 启动模拟时，simulation_runner 会从 scripts/ 目录运行脚本
            
            # 更新状态
            state.status = SimulationStatus.READY
            self._save_simulation_state(state)
            
            logger.info(f"模拟准备完成: {simulation_id}, "
                       f"entities={state.entities_count}, profiles={state.profiles_count}")
            
            return state
            
        except Exception as e:
            logger.error(f"模拟准备失败: {simulation_id}, error={str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            state.status = SimulationStatus.FAILED
            state.error = str(e)
            self._save_simulation_state(state)
            raise
    
    def get_simulation(self, simulation_id: str) -> Optional[SimulationState]:
        """获取模拟状态"""
        return self._load_simulation_state(simulation_id)
    
    def list_simulations(self, project_id: Optional[str] = None) -> List[SimulationState]:
        """列出所有模拟"""
        simulations = []
        
        if os.path.exists(self.SIMULATION_DATA_DIR):
            for sim_id in os.listdir(self.SIMULATION_DATA_DIR):
                # 跳过隐藏文件（如 .DS_Store）和非目录文件
                sim_path = os.path.join(self.SIMULATION_DATA_DIR, sim_id)
                if sim_id.startswith('.') or not os.path.isdir(sim_path):
                    continue
                
                state = self._load_simulation_state(sim_id)
                if state:
                    if project_id is None or state.project_id == project_id:
                        simulations.append(state)
        
        return simulations
    
    def get_profiles(self, simulation_id: str, platform: str = "reddit") -> List[Dict[str, Any]]:
        """获取模拟的Agent Profile"""
        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"模拟不存在: {simulation_id}")
        
        sim_dir = self._get_simulation_dir(simulation_id)
        profile_path = os.path.join(sim_dir, f"{platform}_profiles.json")
        
        if not os.path.exists(profile_path):
            return []
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_simulation_config(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """获取模拟配置"""
        sim_dir = self._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        
        if not os.path.exists(config_path):
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_run_instructions(self, simulation_id: str) -> Dict[str, str]:
        """获取运行说明"""
        sim_dir = self._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts'))
        
        return {
            "simulation_dir": sim_dir,
            "scripts_dir": scripts_dir,
            "config_file": config_path,
            "commands": {
                "twitter": f"python {scripts_dir}/run_twitter_simulation.py --config {config_path}",
                "reddit": f"python {scripts_dir}/run_reddit_simulation.py --config {config_path}",
                "parallel": f"python {scripts_dir}/run_parallel_simulation.py --config {config_path}",
            },
            "instructions": (
                f"1. 激活conda环境: conda activate MiroFish\n"
                f"2. 运行模拟 (脚本位于 {scripts_dir}):\n"
                f"   - 单独运行Twitter: python {scripts_dir}/run_twitter_simulation.py --config {config_path}\n"
                f"   - 单独运行Reddit: python {scripts_dir}/run_reddit_simulation.py --config {config_path}\n"
                f"   - 并行运行双平台: python {scripts_dir}/run_parallel_simulation.py --config {config_path}"
            )
        }

# MIROFISH_V17_ZERO_AGENT_FALLBACK_START
# Targeted patch: if graph filtering yields zero agent entities, create a tiny
# safe fallback environment instead of leaving Env Setup polling forever.

def _mirofish_v17_write_json(path, data):
    import json
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _mirofish_v17_write_csv(path, rows):
    import csv
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fields = [
        "user_id", "username", "name", "bio", "persona",
        "friend_count", "follower_count", "statuses_count",
        "created_at", "age", "gender", "mbti", "country", "profession"
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})

def _mirofish_v17_make_profiles(seed_text, count=6):
    base = (seed_text or "Uploaded seed").strip()
    if len(base) > 180:
        base = base[:180] + "..."
    roles = [
        ("analyst", "Analyst", "neutral", 2.0),
        ("skeptic", "Skeptic", "opposing", 1.1),
        ("supporter", "Supporter", "supportive", 1.2),
        ("observer", "Observer", "observer", 0.8),
        ("media_voice", "Media Voice", "neutral", 1.7),
        ("practical_user", "Practical User", "neutral", 1.0),
    ]
    profiles = []
    agent_configs = []
    for i in range(count):
        slug, role_name, stance, influence = roles[i % len(roles)]
        name = f"{role_name} {i + 1}"
        username = f"{slug}_{i + 1}"
        bio = f"{role_name} profile generated by safe zero-entity fallback."
        persona = (
            f"{name} evaluates the uploaded seed and simulation requirement. "
            f"Context: {base}"
        )
        profile = {
            "user_id": i,
            "username": username,
            "name": name,
            "bio": bio,
            "persona": persona,
            "karma": 1000 + i * 100,
            "friend_count": 100 + i * 10,
            "follower_count": 150 + i * 20,
            "statuses_count": 500 + i * 50,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "age": 25 + i,
            "gender": "other",
            "mbti": "INTJ",
            "country": "Global",
            "profession": role_name,
            "interested_topics": ["analysis", "simulation", "public reaction"],
        }
        profiles.append(profile)
        agent_configs.append({
            "agent_id": i,
            "entity_uuid": f"fallback_entity_{i}",
            "entity_name": name,
            "entity_type": "SyntheticPerson",
            "activity_level": 0.55,
            "posts_per_hour": 0.4,
            "comments_per_hour": 0.8,
            "active_hours": list(range(8, 23)),
            "response_delay_min": 5,
            "response_delay_max": 60,
            "sentiment_bias": 0.0,
            "stance": stance,
            "influence_weight": influence,
        })
    return profiles, agent_configs

def _mirofish_v17_write_ready_fallback(self, state, simulation_requirement, document_text, reason):
    import os
    sim_dir = self._get_simulation_dir(state.simulation_id)
    seed = simulation_requirement or document_text or "No seed text"
    profiles, agent_configs = _mirofish_v17_make_profiles(seed, count=6)

    _mirofish_v17_write_json(os.path.join(sim_dir, "reddit_profiles.json"), profiles)

    twitter_rows = []
    for p in profiles:
        row = dict(p)
        row["user_id"] = p["user_id"]
        row["username"] = p["username"]
        row["friend_count"] = p.get("friend_count", 100)
        row["follower_count"] = p.get("follower_count", 150)
        row["statuses_count"] = p.get("statuses_count", 500)
        twitter_rows.append(row)
    _mirofish_v17_write_csv(os.path.join(sim_dir, "twitter_profiles.csv"), twitter_rows)

    config = {
        "simulation_id": state.simulation_id,
        "project_id": state.project_id,
        "graph_id": state.graph_id,
        "simulation_requirement": simulation_requirement or "",
        "time_config": {
            "total_simulation_hours": 24,
            "minutes_per_round": 60,
            "agents_per_hour_min": 1,
            "agents_per_hour_max": 3,
            "peak_hours": [18, 19, 20, 21, 22],
            "peak_activity_multiplier": 1.5,
            "off_peak_hours": [0, 1, 2, 3, 4, 5],
            "off_peak_activity_multiplier": 0.05,
            "morning_hours": [6, 7, 8],
            "morning_activity_multiplier": 0.4,
            "work_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17],
            "work_activity_multiplier": 0.7
        },
        "agent_configs": agent_configs,
        "event_config": {
            "initial_posts": [
                {
                    "content": (simulation_requirement or "Initial simulation event")[:500],
                    "poster_type": "SyntheticPerson",
                    "poster_agent_id": 0
                }
            ],
            "scheduled_events": [],
            "hot_topics": ["simulation", "reaction", "scenario"],
            "narrative_direction": simulation_requirement or "Explore possible reactions."
        },
        "twitter_config": {
            "platform": "twitter",
            "recency_weight": 0.4,
            "popularity_weight": 0.3,
            "relevance_weight": 0.3,
            "viral_threshold": 10,
            "echo_chamber_strength": 0.5
        } if state.enable_twitter else None,
        "reddit_config": {
            "platform": "reddit",
            "recency_weight": 0.3,
            "popularity_weight": 0.4,
            "relevance_weight": 0.3,
            "viral_threshold": 15,
            "echo_chamber_strength": 0.6
        } if state.enable_reddit else None,
        "llm_model": getattr(Config, "LLM_MODEL_NAME", ""),
        "llm_base_url": getattr(Config, "LLM_BASE_URL", ""),
        "generated_at": datetime.now().isoformat(),
        "generation_reasoning": f"v17 safe fallback used: {reason}"
    }
    _mirofish_v17_write_json(os.path.join(sim_dir, "simulation_config.json"), config)

    state.entities_count = len(profiles)
    state.profiles_count = len(profiles)
    state.entity_types = ["SyntheticPerson"]
    state.config_generated = True
    state.config_reasoning = config["generation_reasoning"]
    state.status = SimulationStatus.READY
    state.error = None
    self._save_simulation_state(state)
    logger.warning(
        "v17 zero-entity fallback prepared simulation %s with %s synthetic agents",
        state.simulation_id,
        len(profiles),
    )
    return state

if not hasattr(SimulationManager, "_mirofish_v17_original_prepare"):
    SimulationManager._mirofish_v17_original_prepare = SimulationManager.prepare_simulation

def _mirofish_v17_prepare_simulation(
    self,
    simulation_id,
    simulation_requirement,
    document_text,
    defined_entity_types=None,
    use_llm_for_profiles=True,
    progress_callback=None,
    parallel_profile_count=3,
):
    state_before = self._load_simulation_state(simulation_id)
    try:
        result = SimulationManager._mirofish_v17_original_prepare(
            self,
            simulation_id=simulation_id,
            simulation_requirement=simulation_requirement,
            document_text=document_text,
            defined_entity_types=defined_entity_types,
            use_llm_for_profiles=use_llm_for_profiles,
            progress_callback=progress_callback,
            parallel_profile_count=parallel_profile_count,
        )
    except Exception as exc:
        state_after = self._load_simulation_state(simulation_id) or state_before
        if state_after and (getattr(state_after, "entities_count", 0) == 0 or "entity" in str(exc).lower()):
            if progress_callback:
                progress_callback("generating_config", 100, "Safe fallback config generated", current=3, total=3)
            return _mirofish_v17_write_ready_fallback(
                self,
                state_after,
                simulation_requirement,
                document_text,
                f"prepare exception: {str(exc)[:200]}",
            )
        raise

    if result and (not getattr(result, "config_generated", False) or getattr(result, "profiles_count", 0) == 0):
        if getattr(result, "entities_count", 0) == 0 or getattr(result, "profiles_count", 0) == 0:
            if progress_callback:
                progress_callback("generating_config", 100, "Safe fallback config generated", current=3, total=3)
            return _mirofish_v17_write_ready_fallback(
                self,
                result,
                simulation_requirement,
                document_text,
                "zero profiles or config not generated",
            )
    return result

SimulationManager.prepare_simulation = _mirofish_v17_prepare_simulation
# MIROFISH_V17_ZERO_AGENT_FALLBACK_END
