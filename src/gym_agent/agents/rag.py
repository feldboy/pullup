"""
RAG Agent for GymAI - Knowledge Base Search.

Handles questions using the gym's PDF documentation.
For MVP: Uses in-memory storage with simple text matching.
For Production: Will use Supabase pgvector for semantic search.
"""

from dataclasses import dataclass
from pathlib import Path
import re

from pydantic_ai import Agent, RunContext

from gym_agent.config import settings
from gym_agent.models.responses import RAGResponse, RAGSearchResult


@dataclass
class RAGDependencies:
    """Dependencies for RAG agent."""
    gym_id: str = "eloozfit"


# EloozFit Knowledge Base (extracted from PDF)
# In production this would come from Supabase pgvector
ELOOZFIT_KNOWLEDGE = {
    "about": {
        "name": "EloozFit (אילוזפיט)",
        "name_hebrew": "אילוזפיט",
        "location": "מושב נורדיה, בתוך מתחם 'מגדלי הים התיכון'",
        "founded": "2021",
        "years_active": "4+",
        "members": "כ-300 מנויים פעילים",
        "atmosphere": "אווירה קהילתית, מקצועית ומשפחתית",
        "vision": "מעטפת כושר הוליסטית המשלבת בין כוח, גמישות, והכנה מנטלית ופיזית לכל שלבי החיים",
    },
    
    "hours": {
        "sunday_thursday": "08:00 - 21:00 (רצוף)",
        "friday": "08:00 - 14:00",
        "saturday": "סגור",
        "summary_hebrew": "ראשון-חמישי: 08:00-21:00, שישי: 08:00-14:00, שבת: סגור",
        "summary_english": "Sun-Thu: 8AM-9PM, Fri: 8AM-2PM, Sat: Closed",
    },
    
    "services": {
        "functional_training": {
            "name": "אימונים פונקציונליים",
            "description": "אימוני קבוצה דינמיים המתמקדים בשיפור תנועות יומיומיות, חיזוק השרירים, סיבולת לב-ריאה ושריפת קלוריות גבוהה",
        },
        "pilates": {
            "name": "פילאטיס מכשירים",
            "description": "עבודה על חיזוק שרירי הליבה, הארכת השרירים, שיפור היציבה וגמישות המפרקים באמצעות מיטות רפורמר מתקדמות",
        },
        "yoga": {
            "name": "יוגה",
            "description": "תרגול המשלב גוף ונפש, שיפור טווחי תנועה, הפחתת סטרס וחיזוק סטטי",
        },
        "open_gym": {
            "name": "Open Gym (אימון חופשי)",
            "description": "אפשרות למנויים להתאמן באופן עצמאי במתחם המכשירים והמשקולות החופשיים של הסטודיו בשעות הפעילות",
        },
        "combat_fitness": {
            "name": "כושר קרבי",
            "description": "תוכנית ייעודית לבני נוער לפני גיוס, המתמקדת בחוסן מנטלי, ריצות, זחילות, ועבודה עם משקלים כהכנה לימי סיירות ושירות משמעותי",
        },
        "personal_training": {
            "name": "אימונים אישיים",
            "description": "אימונים 1-על-1 עם צוות המאמנים המקצועי לעבודה על מטרות ספציפיות",
        },
    },
    
    "memberships": {
        "unlimited": {
            "name": "מנוי Unlimited",
            "description": "כניסה חופשית לכל סוגי האימונים (כולל פילאטיס מכשירים) ושימוש ב-Open Gym",
            "includes_pilates": True,
        },
        "core": {
            "name": "מנוי Core",
            "description": "התמקדות באימונים פונקציונליים ויוגה + Open Gym (לא כולל פילאטיס מכשירים)",
            "includes_pilates": False,
        },
        "pilates_card": {
            "name": "כרטיסיית פילאטיס",
            "description": "כרטיסייה של 10 או 20 כניסות לשימוש גמיש",
        },
        "pre_army": {
            "name": "מסלול 'לפני צבא'",
            "description": "מנוי מוזל המיועד למתאמני הכושר הקרבי",
        },
    },
    
    "policies": {
        "registration": "הרישום לכל השיעורים (פונקציונלי, פילאטיס, יוגה) מתבצע דרך אפליקציית הסטודיו (EloozFit App)",
        "cancellation": "ניתן לבטל שיעור עד 4 שעות לפני תחילתו ללא חיוב. ביטול מאוחר ייחשב כניצול הכניסה",
        "equipment": "יש להגיע עם בגדי ספורט נוחים, נעלי ספורט סגורות, מגבת אישית ובקבוק מים. בשיעורי פילאטיס ויוגה ניתן להתאמן עם גרביים מונעות החלקה",
        "parking": "קיימת חניה חופשית ובשפע לבאי הסטודיו בתוך מתחם מגדלי הים התיכון",
        "open_gym_booking": "בדרך כלל אין צורך בהזמנה מראש ל-Open Gym, אך מומלץ להתעדכן באפליקציה בשעות העומס",
    },
    
    "facilities": {
        "description": "הסטודיו מאובזר במלתחות חדישות, מקלחות, פינת קפה ומנוחה, ומערכת סאונד מתקדמת",
        "amenities": ["מלתחות חדישות", "מקלחות", "פינת קפה ומנוחה", "מערכת סאונד מתקדמת"],
    },
    
    "faq": {
        "beginners": {
            "question": "האם הסטודיו מתאים למתחילים?",
            "answer": "בהחלט! המאמנים ב-EloozFit יודעים לבצע התאמות (Scale) לכל תרגיל בהתאם לרמת המתאמן, כך שכל אחד יכול להשתלב בבטחה.",
        },
        "open_gym_booking": {
            "question": "האם צריך להזמין מקום ל-Open Gym?",
            "answer": "בדרך כלל אין צורך בהזמנה מראש ל-Open Gym, אך מומלץ להתעדכן באפליקציה בשעות העומס.",
        },
        "personal_training": {
            "question": "האם יש אימונים אישיים?",
            "answer": "כן, ניתן לתאם אימונים אישיים (1-על-1) עם צוות המאמנים המקצועי של הסטודיו לטובת עבודה על מטרות ספציפיות.",
        },
    },
}


class RAGService:
    """
    RAG Service for searching gym knowledge base.
    
    MVP: In-memory keyword search
    Production: Supabase pgvector semantic search
    """
    
    def __init__(self, knowledge_base: dict = None):
        """Initialize with knowledge base."""
        self.knowledge = knowledge_base or ELOOZFIT_KNOWLEDGE
    
    def search(self, query: str, top_k: int = 3) -> list[RAGSearchResult]:
        """
        Search the knowledge base for relevant information.
        
        Args:
            query: User's question
            top_k: Number of results to return
            
        Returns:
            List of search results with content and relevance scores
        """
        query_lower = query.lower()
        results = []
        
        # Keyword mapping for common queries
        keyword_mappings = {
            # Hours
            ("שעות", "פתוח", "סגור", "פעילות", "hours", "open", "close", "when"): "hours",
            # Location
            ("איפה", "מיקום", "כתובת", "location", "where", "address"): "about",
            # Services/Classes
            ("שיעורים", "אימונים", "שיעור", "classes", "workout", "training", "חוגים", "חוג", "איזה יש", "מה יש"): "services",
            ("פילאטיס", "pilates"): ("services", "pilates"),
            ("יוגה", "yoga"): ("services", "yoga"),
            ("פונקציונלי", "functional"): ("services", "functional_training"),
            ("אישי", "personal", "1על1", "1-על-1"): ("services", "personal_training"),
            ("קרבי", "צבא", "combat", "army", "military"): ("services", "combat_fitness"),
            ("open gym", "אימון חופשי", "משקולות"): ("services", "open_gym"),
            # Memberships
            ("מנוי", "מחיר", "עלות", "membership", "price", "cost", "plan", "כמה עולה"): "memberships",
            # Policies
            ("ביטול", "cancel", "לבטל"): "policies",
            ("הזמנה", "רישום", "להירשם", "book", "register", "sign up"): "policies",
            ("ציוד", "מה להביא", "equipment", "bring"): "policies",
            ("חניה", "parking"): "policies",
            # Facilities
            ("מתקנים", "מלתחות", "מקלחות", "facilities", "shower", "locker"): "facilities",
            # FAQ - Beginners
            ("מתחיל", "התחלה", "beginner", "new", "חדש"): ("faq", "beginners"),
        }
        
        # Find matching sections
        matched_sections = set()
        for keywords, section in keyword_mappings.items():
            if any(kw in query_lower for kw in keywords):
                if isinstance(section, tuple):
                    matched_sections.add(section)
                else:
                    matched_sections.add((section,))
        
        # If no specific match, search all sections
        if not matched_sections:
            matched_sections = {
                ("about",), ("hours",), ("services",), 
                ("memberships",), ("policies",), ("faq",)
            }
        
        # Extract content from matched sections
        for section_path in matched_sections:
            content = self._get_section_content(section_path)
            if content:
                # Calculate simple relevance score based on keyword overlap
                score = self._calculate_relevance(query_lower, content.lower())
                results.append(RAGSearchResult(
                    content=content,
                    source_file="eloozfit-knowledge-doc.pdf",
                    relevance_score=min(1.0, score),
                ))
        
        # Sort by relevance and return top_k
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_k]
    
    def _get_section_content(self, section_path: tuple) -> str:
        """Get formatted content from a section path."""
        data = self.knowledge
        
        for key in section_path:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return ""
        
        # Format the data as readable text
        if isinstance(data, dict):
            lines = []
            for k, v in data.items():
                if isinstance(v, dict):
                    if "name" in v and "description" in v:
                        lines.append(f"{v['name']}: {v['description']}")
                    elif "question" in v and "answer" in v:
                        lines.append(f"ש: {v['question']}\nת: {v['answer']}")
                    else:
                        lines.append(f"{k}: {v}")
                elif isinstance(v, list):
                    lines.append(f"{k}: {', '.join(v)}")
                else:
                    lines.append(f"{k}: {v}")
            return "\n".join(lines)
        
        return str(data)
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate simple keyword overlap relevance score."""
        query_words = set(re.findall(r'\w+', query))
        content_words = set(re.findall(r'\w+', content))
        
        if not query_words:
            return 0.0
        
        overlap = len(query_words & content_words)
        return overlap / len(query_words) * 0.8 + 0.2  # Base score of 0.2
    
    def get_hours(self) -> str:
        """Get formatted operating hours."""
        hours = self.knowledge["hours"]
        return (
            f"שעות פעילות:\n"
            f"• ראשון-חמישי: {hours['sunday_thursday']}\n"
            f"• שישי: {hours['friday']}\n"
            f"• שבת: {hours['saturday']}"
        )
    
    def get_services_list(self) -> str:
        """Get formatted list of services."""
        services = self.knowledge["services"]
        lines = ["סוגי אימונים ב-EloozFit:"]
        for key, service in services.items():
            lines.append(f"• {service['name']}")
        return "\n".join(lines)
    
    def get_membership_info(self) -> str:
        """Get formatted membership information."""
        memberships = self.knowledge["memberships"]
        lines = ["מסלולי מנויים:"]
        for key, plan in memberships.items():
            lines.append(f"• {plan['name']}: {plan['description']}")
        return "\n".join(lines)


# Convenience function for direct RAG search
def search_gym_info(query: str) -> RAGResponse:
    """
    Search gym information and return structured response.
    
    Args:
        query: User's question
        
    Returns:
        RAGResponse with answer and sources
    """
    rag_service = RAGService()
    results = rag_service.search(query, top_k=3)
    
    if not results or results[0].relevance_score < 0.3:
        return RAGResponse(
            answer="מצטער, לא מצאתי מידע על זה. אעביר את השאלה לצוות והם יחזרו אליך.",
            sources=[],
            found_in_knowledge_base=False,
            confidence=0.0,
        )
    
    # Combine results into answer
    answer = results[0].content
    
    return RAGResponse(
        answer=answer,
        sources=results,
        found_in_knowledge_base=True,
        confidence=results[0].relevance_score,
    )


# Export the service and search function
__all__ = ["RAGService", "search_gym_info", "ELOOZFIT_KNOWLEDGE"]
