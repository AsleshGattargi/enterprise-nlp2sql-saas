from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from src.models import User, HumanDigitalTwin, Agent, HDTAgent, UserHDTAssignment
from src.database import db_manager
import logging
import json

logger = logging.getLogger(__name__)

class HDTManager:
    """Human Digital Twin Manager - handles HDT operations and agent assignments"""
    
    def __init__(self):
        self.agent_capabilities = {
            'nlp2sql': {
                'description': 'Converts natural language to SQL queries with dialect awareness',
                'capabilities': ['query_generation', 'dialect_conversion', 'syntax_validation'],
                'supported_dialects': ['mysql', 'postgresql', 'mongodb']
            },
            'rag': {
                'description': 'Retrieval Augmented Generation for contextual query enhancement',
                'capabilities': ['document_retrieval', 'context_enhancement', 'knowledge_base'],
                'use_cases': ['complex_queries', 'domain_specific_knowledge']
            },
            'analytics': {
                'description': 'Advanced analytics and data insights',
                'capabilities': ['statistical_analysis', 'trend_analysis', 'forecasting'],
                'analysis_types': ['descriptive', 'predictive', 'diagnostic']
            },
            'reporting': {
                'description': 'Automated report generation and visualization',
                'capabilities': ['report_generation', 'data_visualization', 'export_formats'],
                'formats': ['csv', 'pdf', 'excel', 'html']
            },
            'chatbot': {
                'description': 'Conversational interface for data queries',
                'capabilities': ['natural_conversation', 'query_clarification', 'help_assistance'],
                'features': ['conversation_memory', 'clarification_prompts']
            }
        }
    
    def get_user_hdt(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get HDT profile for a user"""
        try:
            with db_manager.get_metadata_db() as db:
                # Get user's HDT assignment
                assignment = db.query(UserHDTAssignment).filter(
                    UserHDTAssignment.user_id == user_id
                ).first()
                
                if not assignment:
                    return None
                
                # Get HDT details
                hdt = db.query(HumanDigitalTwin).filter(
                    HumanDigitalTwin.hdt_id == assignment.hdt_id
                ).first()
                
                if not hdt:
                    return None
                
                # Get assigned agents
                agents = db.query(Agent).join(HDTAgent).filter(
                    HDTAgent.hdt_id == hdt.hdt_id
                ).all()
                
                return {
                    'hdt_id': hdt.hdt_id,
                    'name': hdt.name,
                    'description': hdt.description,
                    'context': hdt.context,
                    'skillset': hdt.skillset if hdt.skillset else [],
                    'languages': hdt.languages if hdt.languages else [],
                    'agents': [
                        {
                            'agent_id': agent.agent_id,
                            'agent_name': agent.agent_name,
                            'agent_type': agent.agent_type,
                            'description': agent.description,
                            'capabilities': agent.capabilities if agent.capabilities else [],
                            'config': agent.config if agent.config else {}
                        }
                        for agent in agents
                    ]
                }
        except Exception as e:
            logger.error(f"Error getting HDT for user {user_id}: {e}")
            return None
    
    def get_available_agents(self, hdt_id: str) -> List[Dict[str, Any]]:
        """Get list of agents available to an HDT"""
        try:
            with db_manager.get_metadata_db() as db:
                agents = db.query(Agent).join(HDTAgent).filter(
                    HDTAgent.hdt_id == hdt_id
                ).all()
                
                agent_list = []
                for agent in agents:
                    agent_info = {
                        'agent_id': agent.agent_id,
                        'agent_name': agent.agent_name,
                        'agent_type': agent.agent_type,
                        'description': agent.description,
                        'capabilities': agent.capabilities if agent.capabilities else [],
                        'config': agent.config if agent.config else {}
                    }
                    
                    # Enhance with predefined capabilities
                    if agent.agent_type in self.agent_capabilities:
                        predefined = self.agent_capabilities[agent.agent_type]
                        agent_info['enhanced_description'] = predefined['description']
                        agent_info['enhanced_capabilities'] = predefined['capabilities']
                        
                        # Add specific features based on agent type
                        for key, value in predefined.items():
                            if key not in ['description', 'capabilities']:
                                agent_info[key] = value
                    
                    agent_list.append(agent_info)
                
                return agent_list
        except Exception as e:
            logger.error(f"Error getting agents for HDT {hdt_id}: {e}")
            return []
    
    def check_agent_permission(self, user_id: str, agent_type: str) -> bool:
        """Check if user's HDT has access to specific agent type"""
        try:
            user_hdt = self.get_user_hdt(user_id)
            if not user_hdt:
                return False
            
            for agent in user_hdt['agents']:
                if agent['agent_type'] == agent_type:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking agent permission for user {user_id}: {e}")
            return False
    
    def get_hdt_context(self, user_id: str) -> str:
        """Get HDT context for prompt engineering"""
        try:
            user_hdt = self.get_user_hdt(user_id)
            if not user_hdt:
                return "You are a general assistant helping with data queries."
            
            # Build context string
            context_parts = []
            
            # Add HDT description and context
            if user_hdt.get('description'):
                context_parts.append(f"Profile: {user_hdt['description']}")
            
            if user_hdt.get('context'):
                context_parts.append(f"Context: {user_hdt['context']}")
            
            # Add skillset
            if user_hdt.get('skillset'):
                skills = ', '.join(user_hdt['skillset'])
                context_parts.append(f"Skills: {skills}")
            
            # Add programming languages
            if user_hdt.get('languages'):
                languages = ', '.join(user_hdt['languages'])
                context_parts.append(f"Languages: {languages}")
            
            # Add available agents
            if user_hdt.get('agents'):
                agent_types = [agent['agent_type'] for agent in user_hdt['agents']]
                context_parts.append(f"Available tools: {', '.join(agent_types)}")
            
            return '. '.join(context_parts) + '.'
            
        except Exception as e:
            logger.error(f"Error getting HDT context for user {user_id}: {e}")
            return "You are a general assistant helping with data queries."
    
    def customize_query_approach(self, user_id: str, query_text: str) -> Dict[str, Any]:
        """Customize query approach based on HDT profile"""
        try:
            user_hdt = self.get_user_hdt(user_id)
            if not user_hdt:
                return {
                    'approach': 'basic',
                    'suggested_agents': ['nlp2sql'],
                    'complexity_level': 'simple'
                }
            
            hdt_name = user_hdt.get('name', '').lower()
            available_agents = [agent['agent_type'] for agent in user_hdt.get('agents', [])]
            skillset = user_hdt.get('skillset', [])
            
            # Determine approach based on HDT profile
            if 'researcher' in hdt_name or 'analyst' in hdt_name:
                approach = 'analytical'
                suggested_agents = ['nlp2sql', 'analytics']
                if 'rag' in available_agents:
                    suggested_agents.append('rag')
                complexity_level = 'advanced'
                
            elif 'data_scientist' in hdt_name:
                approach = 'data_science'
                suggested_agents = ['nlp2sql', 'analytics', 'rag']
                complexity_level = 'expert'
                
            elif 'financial' in hdt_name:
                approach = 'financial'
                suggested_agents = ['nlp2sql', 'reporting']
                complexity_level = 'intermediate'
                
            elif 'manager' in hdt_name or 'business' in hdt_name:
                approach = 'business'
                suggested_agents = ['nlp2sql', 'reporting', 'chatbot']
                complexity_level = 'intermediate'
                
            else:  # basic_user
                approach = 'simple'
                suggested_agents = ['nlp2sql', 'chatbot']
                complexity_level = 'simple'
            
            # Filter suggested agents to only include available ones
            suggested_agents = [agent for agent in suggested_agents if agent in available_agents]
            
            # Analyze query complexity
            query_lower = query_text.lower()
            complexity_keywords = {
                'simple': ['show', 'list', 'what', 'how many'],
                'intermediate': ['compare', 'analyze', 'trend', 'group by', 'average'],
                'advanced': ['correlation', 'forecast', 'predict', 'complex', 'join'],
                'expert': ['machine learning', 'statistical', 'regression', 'model']
            }
            
            detected_complexity = 'simple'
            for level, keywords in complexity_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    detected_complexity = level
            
            return {
                'approach': approach,
                'suggested_agents': suggested_agents,
                'complexity_level': max(complexity_level, detected_complexity, key=lambda x: ['simple', 'intermediate', 'advanced', 'expert'].index(x)),
                'hdt_context': self.get_hdt_context(user_id),
                'personalization': {
                    'role_focus': hdt_name,
                    'technical_level': 'high' if any(skill in ['coding', 'programming', 'data_science'] for skill in skillset) else 'medium',
                    'preferred_output': 'detailed' if 'researcher' in hdt_name else 'summary'
                }
            }
            
        except Exception as e:
            logger.error(f"Error customizing query approach for user {user_id}: {e}")
            return {
                'approach': 'basic',
                'suggested_agents': ['nlp2sql'],
                'complexity_level': 'simple'
            }
    
    def get_hdt_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available HDT templates for setup"""
        return {
            'researcher_analyst': {
                'name': 'researcher_analyst',
                'description': 'Research and analytics expert',
                'context': 'You are an analyst who works in an analytical way, focusing on data-driven insights and research methodologies',
                'skillset': ['coding', 'research', 'data_analysis', 'statistics'],
                'languages': ['python', 'sql', 'r'],
                'agents': ['nlp2sql', 'rag', 'analytics']
            },
            'business_manager': {
                'name': 'business_manager',
                'description': 'Business operations and management',
                'context': 'You are a business manager focused on operational efficiency and strategic decision making',
                'skillset': ['management', 'strategy', 'operations', 'finance'],
                'languages': ['sql', 'excel'],
                'agents': ['nlp2sql', 'reporting', 'chatbot']
            },
            'data_scientist': {
                'name': 'data_scientist',
                'description': 'Advanced data science and ML',
                'context': 'You are a data scientist specializing in machine learning and advanced analytics',
                'skillset': ['machine_learning', 'statistics', 'programming', 'visualization'],
                'languages': ['python', 'r', 'scala', 'sql'],
                'agents': ['nlp2sql', 'rag', 'analytics']
            },
            'financial_analyst': {
                'name': 'financial_analyst',
                'description': 'Financial analysis and reporting',
                'context': 'You are a financial analyst focused on financial modeling and reporting',
                'skillset': ['finance', 'accounting', 'modeling', 'reporting'],
                'languages': ['sql', 'python', 'excel'],
                'agents': ['nlp2sql', 'reporting']
            },
            'basic_user': {
                'name': 'basic_user',
                'description': 'General business user',
                'context': 'You are a general business user who needs simple data access and reporting',
                'skillset': ['basic_analysis', 'reporting'],
                'languages': ['sql'],
                'agents': ['nlp2sql', 'chatbot']
            }
        }

# Global HDT manager instance
hdt_manager = HDTManager()