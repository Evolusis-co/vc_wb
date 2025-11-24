"""
Feedback Analysis System for VoiceCoach
Analyzes conversations and generates comprehensive feedback (no storage)
OPTIMIZED: Uses async parallel processing
"""

import re
import asyncio
from typing import List, Dict
from .advanced_analysis_async import AdvancedConversationAnalyzer


class FeedbackGenerator:
    """Generate comprehensive feedback from conversation data"""
    
    def __init__(self):
        self.advanced_analyzer = AdvancedConversationAnalyzer()
        
        # Filler word patterns
        self.filler_patterns = [
            r'\bum+\b', r'\buh+\b', r'\ber+\b', r'\bah+\b',
            r'\blike\b', r'\byou know\b', r'\bi mean\b',
            r'\bactually\b', r'\bbasically\b', r'\bliterally\b',
            r'\bseriously\b', r'\bhonestly\b', r'\bkinda\b',
            r'\bsorta\b', r'\bwell\b', r'\bso\b', r'\bjust\b',
            r'\breally\b', r'\bvery\b', r'\btotally\b'
        ]
    
    async def analyze_conversation(self, conversation_data: Dict) -> Dict:
        """
        Analyze a conversation and generate comprehensive feedback (ASYNC)
        
        Args:
            conversation_data: Dict with 'turns', 'scenario', etc.
        
        Returns:
            Dict with comprehensive feedback
        """
        # Analyze filler words in user turns
        for turn in conversation_data["turns"]:
            if turn["role"] == "user":
                turn = self._detect_filler_words(turn)
        
        user_turns = [t for t in conversation_data["turns"] if t["role"] == "user"]
        
        feedback = {
            "generated_at": conversation_data.get("start_time", ""),
            "summary": self._generate_summary(conversation_data),
            "filler_words_analysis": self._analyze_filler_words(user_turns),
            "speaking_pace_analysis": self._analyze_speaking_pace(user_turns),
            "communication_quality": self._analyze_communication_quality(conversation_data),
            "conversation_flow": self._analyze_conversation_flow(conversation_data),
            "strengths": [],
            "areas_for_improvement": [],
            "overall_score": 0
        }
        
        # Add advanced AI-powered analysis (AWAIT)
        print("🤖 Running advanced AI analysis...")
        try:
            advanced_analysis = await self.advanced_analyzer.analyze_conversation_async(conversation_data)
            feedback["advanced_analysis"] = advanced_analysis
            print("✅ Advanced AI analysis complete!")
        except Exception as e:
            print(f"⚠️ Advanced analysis error: {e}")
            import traceback
            traceback.print_exc()
            feedback["advanced_analysis"] = {"error": str(e)}
        
        # Generate strengths and improvements
        feedback["strengths"], feedback["areas_for_improvement"] = self._generate_recommendations(feedback)
        
        # Calculate overall score (includes advanced metrics)
        feedback["overall_score"] = self._calculate_overall_score(feedback)
        
        return feedback
    
    def _detect_filler_words(self, turn: Dict) -> Dict:
        """Detect filler words in a turn"""
        text = turn["text"].lower()
        filler_words = []
        
        for pattern in self.filler_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                filler = match.group()
                filler_words.append({
                    "word": filler,
                    "position": match.start(),
                    "context": text[max(0, match.start()-20):match.end()+20]
                })
        
        turn["filler_words"] = filler_words
        turn["filler_word_count"] = len(filler_words)
        return turn
    
    def _generate_summary(self, conversation: Dict) -> Dict:
        """Generate conversation summary"""
        user_turns = [t for t in conversation["turns"] if t["role"] == "user"]
        
        return {
            "scenario": conversation.get("scenario", {}).get("name", "Unknown"),
            "duration_minutes": round(conversation["metadata"]["duration_seconds"] / 60, 1),
            "total_exchanges": len(user_turns),
            "total_words_spoken": conversation["metadata"]["total_user_words"],
            "total_audio_duration": round(conversation["audio_metadata"]["total_user_audio_duration"], 1)
        }
    
    def _analyze_filler_words(self, user_turns: List[Dict]) -> Dict:
        """Analyze filler word usage"""
        total_filler_count = sum(t.get("filler_word_count", 0) for t in user_turns)
        total_words = sum(t["word_count"] for t in user_turns)
        
        # Collect all filler words
        filler_breakdown = {}
        for turn in user_turns:
            for filler in turn.get("filler_words", []):
                word = filler["word"]
                filler_breakdown[word] = filler_breakdown.get(word, 0) + 1
        
        # Sort by frequency
        top_fillers = sorted(filler_breakdown.items(), key=lambda x: x[1], reverse=True)
        
        filler_percentage = (total_filler_count / total_words * 100) if total_words > 0 else 0
        
        # Rating
        if filler_percentage < 3:
            rating = "Excellent"
        elif filler_percentage < 5:
            rating = "Good"
        elif filler_percentage < 8:
            rating = "Fair"
        else:
            rating = "Needs Improvement"
        
        return {
            "total_filler_words": total_filler_count,
            "filler_percentage": round(filler_percentage, 2),
            "rating": rating,
            "most_common_fillers": [{"word": w, "count": c} for w, c in top_fillers[:5]],
            "filler_breakdown": filler_breakdown
        }
    
    def _analyze_speaking_pace(self, user_turns: List[Dict]) -> Dict:
        """Analyze speaking pace (words per minute)"""
        paces = [t["speaking_pace"] for t in user_turns if t.get("speaking_pace")]
        
        if not paces:
            return {
                "average_pace": 0,
                "rating": "Unknown",
                "note": "Audio duration data not available"
            }
        
        avg_pace = sum(paces) / len(paces)
        
        # Ideal pace: 120-150 WPM
        if 120 <= avg_pace <= 150:
            rating = "Excellent"
            note = "Your speaking pace is ideal for clear communication"
        elif 100 <= avg_pace < 120:
            rating = "Good"
            note = "Slightly slower pace - good for emphasis"
        elif 150 < avg_pace <= 180:
            rating = "Good"
            note = "Slightly faster pace - watch for clarity"
        elif avg_pace < 100:
            rating = "Slow"
            note = "Speaking quite slowly - try to increase pace"
        else:
            rating = "Too Fast"
            note = "Speaking very quickly - slow down for clarity"
        
        return {
            "average_pace": round(avg_pace, 1),
            "min_pace": round(min(paces), 1),
            "max_pace": round(max(paces), 1),
            "rating": rating,
            "note": note
        }
    
    def _analyze_communication_quality(self, conversation: Dict) -> Dict:
        """Analyze overall communication quality"""
        user_turns = [t for t in conversation["turns"] if t["role"] == "user"]
        avg_words = conversation["metadata"]["total_user_words"] / len(user_turns) if user_turns else 0
        
        # Response length quality
        if 15 <= avg_words <= 40:
            length_rating = "Excellent"
            length_note = "Good balance of concise and detailed responses"
        elif 10 <= avg_words < 15:
            length_rating = "Good"
            length_note = "Responses are concise"
        elif 40 < avg_words <= 60:
            length_rating = "Good"
            length_note = "Responses are detailed"
        elif avg_words < 10:
            length_rating = "Too Brief"
            length_note = "Responses are very brief"
        else:
            length_rating = "Too Verbose"
            length_note = "Responses are very long"
        
        return {
            "average_words_per_response": round(avg_words, 1),
            "length_rating": length_rating,
            "length_note": length_note
        }
    
    def _analyze_conversation_flow(self, conversation: Dict) -> Dict:
        """Analyze conversation flow and engagement"""
        total_turns = len(conversation["turns"])
        user_turns = len([t for t in conversation["turns"] if t["role"] == "user"])
        
        if user_turns >= 10:
            engagement = "High Engagement"
        elif user_turns >= 5:
            engagement = "Good Engagement"
        else:
            engagement = "Low Engagement"
        
        return {
            "total_exchanges": user_turns,
            "engagement_level": engagement,
            "conversation_completion": "Completed"
        }
    
    def _generate_recommendations(self, feedback: Dict) -> tuple:
        """Generate strengths and improvement areas"""
        strengths = []
        improvements = []
        
        # Filler words
        if feedback["filler_words_analysis"]["filler_percentage"] < 3:
            strengths.append("Excellent control of filler words - very professional")
        elif feedback["filler_words_analysis"]["filler_percentage"] > 5:
            improvements.append(f"Reduce filler words (currently {feedback['filler_words_analysis']['filler_percentage']}%)")
        
        # Speaking pace
        if feedback["speaking_pace_analysis"]["rating"] == "Excellent":
            strengths.append("Perfect speaking pace for clear communication")
        elif feedback["speaking_pace_analysis"]["rating"] in ["Too Fast", "Slow"]:
            improvements.append(feedback["speaking_pace_analysis"]["note"])
        
        # Advanced analysis
        if "advanced_analysis" in feedback and "error" not in feedback["advanced_analysis"]:
            adv = feedback["advanced_analysis"]
            
            if adv.get("grammar_analysis", {}).get("score", 0) > 85:
                strengths.append("Excellent grammar and sentence structure")
            elif adv.get("grammar_analysis", {}).get("score", 0) < 70:
                improvements.append("Work on grammar accuracy")
            
            if adv.get("empathy_analysis", {}).get("score", 0) > 70:
                strengths.append("Great use of empathetic language")
            elif adv.get("empathy_analysis", {}).get("score", 0) < 40:
                improvements.append("Add more empathetic phrases to build rapport")
        
        return strengths, improvements
    
    def _calculate_overall_score(self, feedback: Dict) -> int:
        """Calculate overall performance score (0-100)"""
        score = 100
        
        # Deduct for filler words
        filler_pct = feedback["filler_words_analysis"]["filler_percentage"]
        if filler_pct > 8:
            score -= 20
        elif filler_pct > 5:
            score -= 10
        elif filler_pct > 3:
            score -= 5
        
        # Deduct for poor speaking pace
        pace_rating = feedback["speaking_pace_analysis"]["rating"]
        if pace_rating == "Too Fast":
            score -= 15
        elif pace_rating == "Slow":
            score -= 10
        
        # If advanced analysis available, use it as primary score
        if "advanced_analysis" in feedback and "overall_advanced_score" in feedback["advanced_analysis"]:
            advanced_score = feedback["advanced_analysis"]["overall_advanced_score"]
            # Blend: 70% advanced, 30% basic
            score = (advanced_score * 0.7) + (score * 0.3)
        
        return max(0, min(100, int(score)))
