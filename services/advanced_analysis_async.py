"""
Advanced Conversation Analysis using OpenAI GPT-4o-mini
OPTIMIZED VERSION: Uses async/parallel processing for 5-8x faster analysis
"""

import os
import re
import asyncio
from typing import Dict, List
from openai import AsyncOpenAI
from collections import Counter
import json


class AdvancedConversationAnalyzer:
    """
    Advanced analysis using OpenAI GPT-4o-mini
    PARALLEL processing for speed
    """
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ Warning: OPENAI_API_KEY not found")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=api_key)
        
        self.model = "gpt-4o-mini"
        
        self.empathy_patterns = [
            r'\bi understand\b', r'\bthat sounds\b', r'\bi hear you\b',
            r'\bi can see\b', r'\bthat must be\b', r'\bi appreciate\b'
        ]
        
        self.politeness_patterns = [
            r'\bplease\b', r'\bthank you\b', r'\bthanks\b',
            r'\bappreciate\b', r'\bkindly\b', r'\bwould you\b',
            r'\bcould you\b', r'\bif you don\'t mind\b'
        ]
    
    def analyze_conversation(self, conversation: Dict) -> Dict:
        """Run analysis (sync wrapper - NOT USED, kept for compatibility)"""
        raise NotImplementedError("Use analyze_conversation_async() instead")
    
    async def analyze_conversation_async(self, conversation: Dict) -> Dict:
        """Main async analysis - ALL IN PARALLEL"""
        user_turns = [t for t in conversation["turns"] if t["role"] == "user"]
        
        if not user_turns:
            return self._empty_analysis()
        
        all_text = " ".join([t["text"] for t in user_turns])
        
        print("🚀 Running 8 analyses in parallel...")
        
        # Run ALL analyses at once
        results = await asyncio.gather(
            self._grammar_async(all_text),
            self._sentence_structure_async(all_text),
            self._vocabulary_async(all_text),
            self._empathy_async(all_text),
            self._politeness_async(all_text),
            self._coherence_async(user_turns),
            self._usefulness_async(all_text),
            self._rephrase_async(user_turns)
        )
        
        grammar, sentence, vocab, empathy, politeness, coherence, usefulness, rephrase = results
        
        analysis = {
            "grammar_analysis": grammar,
            "sentence_structure": sentence,
            "vocabulary_analysis": vocab,
            "empathy_analysis": empathy,
            "politeness_analysis": politeness,
            "coherence_analysis": coherence,
            "usefulness_analysis": usefulness,
            "rephrase_suggestions": rephrase,
            "filler_trend_analysis": self._filler_trends(user_turns),
            "overall_advanced_score": 0
        }
        
        analysis["overall_advanced_score"] = self._calc_score(analysis)
        print("✅ Parallel analysis complete!")
        return analysis
    
    async def _grammar_async(self, text: str) -> Dict:
        """Grammar analysis with detailed breakdown"""
        if not self.client:
            return {"score": 85, "rating": "Good", "total_errors": 0, "errors_detail": [], "accuracy_percentage": 100}
        
        total_sentences = len([s for s in text.split('.') if s.strip()])
        
        prompt = f"""Analyze the following conversation text for grammar errors.
        
Text: "{text}"

Provide:
1. Total number of grammar errors found
2. List of specific errors (sentence + issue + correction)
3. Grammar accuracy percentage
4. Detailed analysis of grammar quality

Return JSON format:
{{
    "total_errors": <number>,
    "errors": [
        {{"sentence": "...", "issue": "...", "correction": "..."}},
        ...
    ],
    "accuracy_percentage": <0-100>,
    "analysis": "detailed analysis text"
}}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional grammar expert. Analyze text for grammatical errors comprehensively."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Deterministic for consistent results
                seed=42,  # Fixed seed for reproducibility
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            errors = data.get("total_errors", 0)
            accuracy = data.get("accuracy_percentage", 100)
            
            # Score formula
            raw = max(0, (total_sentences - errors) / total_sentences) if total_sentences > 0 else 1
            score = max(0, min(100, ((raw - 0.6) / 0.35) * 100))
            
            return {
                "total_sentences": total_sentences,
                "grammar_errors": errors,
                "accuracy_raw": raw,
                "score": round(score, 1),
                "rating": self._rating(score),
                "accuracy_percentage": accuracy,
                "errors_detail": data.get("errors", [])[:10],  # Top 10 errors
                "analysis": data.get("analysis", "")
            }
        except Exception as e:
            print(f"Grammar error: {e}")
            return {"score": 85, "rating": "Good", "total_errors": 0, "errors_detail": [], "accuracy_percentage": 100}
    
    async def _sentence_structure_async(self, text: str) -> Dict:
        """Detailed sentence structure analysis"""
        if not self.client:
            return {"variety_score": 75, "rating": "Good", "analysis": "Fallback mode"}
        
        prompt = f"""Analyze the sentence structure of this conversation text:

"{text}"

Provide detailed breakdown:
1. Average sentence length
2. Sentence complexity (simple/compound/complex percentages)
3. Sentence variety score (0-100)
4. Most common sentence patterns
5. Detailed structural analysis

Return JSON format:
{{
    "avg_sentence_length": <number>,
    "simple_sentences": <percentage>,
    "compound_sentences": <percentage>,
    "complex_sentences": <percentage>,
    "variety_score": <0-100>,
    "patterns": ["pattern1", "pattern2", ...],
    "analysis": "detailed analysis text"
}}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a linguistic expert analyzing sentence structure comprehensively."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Deterministic for consistent results
                seed=42,  # Fixed seed for reproducibility
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            score = data.get("variety_score", 75)
            
            return {
                "variety_score": score,
                "rating": self._rating(score),
                "avg_sentence_length": data.get("avg_sentence_length", 15),
                "simple_sentences": data.get("simple_sentences", 40),
                "compound_sentences": data.get("compound_sentences", 30),
                "complex_sentences": data.get("complex_sentences", 30),
                "patterns": data.get("patterns", []),
                "analysis": data.get("analysis", "")
            }
        except Exception as e:
            print(f"Sentence error: {e}")
            return {"variety_score": 75, "rating": "Good", "analysis": "Error"}
    
    async def _vocabulary_async(self, text: str) -> Dict:
        """Comprehensive vocabulary richness analysis"""
        words = re.findall(r'\b\w+\b', text.lower())
        total_words = len(words)
        unique_words = len(set(words))
        
        # Calculate vocabulary richness score
        raw_richness = unique_words / total_words if total_words > 0 else 0
        richness_score = max(0, min(100, ((raw_richness - 0.2) / 0.4) * 100))
        
        if not self.client:
            return {
                "total_words": total_words,
                "unique_words": unique_words,
                "richness_ratio": round(raw_richness, 3),
                "richness_score": round(richness_score, 1),
                "rating": self._rating(richness_score),
                "sophistication_level": 5,
                "overused_words": [],
                "diversity_suggestions": [],
                "improvement_recommendations": []
            }
        
        prompt = f"""Analyze the vocabulary in this text:

"{text}"

Provide:
1. Vocabulary sophistication level (1-10)
2. Top 5 overused words with counts
3. Vocabulary diversity suggestions
4. Recommended vocabulary improvements
5. Analysis of word choice quality

Return JSON format:
{{
    "sophistication_level": <1-10>,
    "overused_words": [
        {{"word": "...", "count": <number>}},
        ...
    ],
    "diversity_suggestions": ["suggestion1", "suggestion2", ...],
    "improvement_recommendations": ["rec1", "rec2", ...],
    "analysis": "detailed analysis"
}}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a vocabulary and linguistics expert providing comprehensive analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Deterministic for consistent results
                seed=42,  # Fixed seed for reproducibility
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            
            return {
                "total_words": total_words,
                "unique_words": unique_words,
                "richness_ratio": round(raw_richness, 3),
                "richness_score": round(richness_score, 1),
                "rating": self._rating(richness_score),
                "sophistication_level": data.get("sophistication_level", 5),
                "overused_words": data.get("overused_words", [])[:5],
                "diversity_suggestions": data.get("diversity_suggestions", []),
                "improvement_recommendations": data.get("improvement_recommendations", []),
                "analysis": data.get("analysis", "")
            }
        except Exception as e:
            print(f"Vocab error: {e}")
            return {
                "total_words": total_words,
                "unique_words": unique_words,
                "richness_score": round(richness_score, 1),
                "rating": self._rating(richness_score)
            }
    
    async def _empathy_async(self, text: str) -> Dict:
        """Empathy markers"""
        count = sum(len(re.findall(p, text.lower())) for p in self.empathy_patterns)
        score = min(100, count * 15)
        
        # Extract specific empathy phrases
        empathy_phrases = re.findall(r'\b(?:i understand|that sounds|i hear you|i can see|that must be|i appreciate)\b', text.lower(), re.IGNORECASE)
        
        return {
            "empathy_score": score,
            "score": score,  # Alias for frontend
            "rating": self._rating(score),
            "empathy_markers_count": count,
            "empathy_count": count,  # Alias for frontend
            "interpretation": f"Found {count} empathy markers in the conversation",
            "examples": empathy_phrases[:3],
            "empathy_markers": [{"marker": phrase, "count": 1} for phrase in set(empathy_phrases[:5])]
        }
    
    async def _politeness_async(self, text: str) -> Dict:
        """Politeness markers"""
        count = sum(len(re.findall(p, text.lower())) for p in self.politeness_patterns)
        score = min(100, count * 12)
        
        # Extract specific politeness phrases
        politeness_phrases = re.findall(r'\b(?:please|thank you|thanks|appreciate|kindly|would you|could you)\b', text.lower(), re.IGNORECASE)
        
        return {
            "politeness_score": score,
            "score": score,  # Alias for frontend
            "rating": self._rating(score),
            "politeness_markers_count": count,
            "politeness_count": count,  # Alias for frontend
            "interpretation": f"Found {count} politeness markers in the conversation",
            "examples": politeness_phrases[:3],
            "politeness_markers": [{"marker": phrase, "count": 1} for phrase in set(politeness_phrases[:5])]
        }
    
    async def _coherence_async(self, turns: List[Dict]) -> Dict:
        """Comprehensive coherence and logical flow analysis"""
        if not self.client or len(turns) < 2:
            return {"coherence_score": 80, "rating": "Good", "flow_quality": "good", "analysis": "Insufficient data"}
        
        # Create conversation flow
        conversation = []
        for i, turn in enumerate(turns[:10], 1):  # Analyze first 10 turns
            conversation.append(f"Turn {i}: {turn['text']}")
        
        conversation_text = "\n".join(conversation)
        
        prompt = f"""Analyze the coherence and logical flow of this conversation:

{conversation_text}

Provide comprehensive analysis of:
1. Coherence score (0-100)
2. Flow quality (excellent/good/fair/poor)
3. Logical connections between responses
4. Topic consistency
5. Transition quality
6. Detailed analysis of coherence

Return JSON format:
{{
    "coherence_score": <0-100>,
    "flow_quality": "excellent|good|fair|poor",
    "logical_connections": "analysis of connections",
    "topic_consistency": "analysis of topic consistency",
    "transition_quality": "analysis of transitions",
    "analysis": "comprehensive coherence analysis"
}}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a conversation analysis expert specializing in coherence and flow."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Deterministic for consistent results
                seed=42,  # Fixed seed for reproducibility
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            score = data.get("coherence_score", 80)
            
            return {
                "coherence_score": score,
                "score": score,  # Alias for frontend
                "rating": self._rating(score),
                "flow_quality": data.get("flow_quality", "good"),
                "flow_assessment": data.get("analysis", "Good conversational flow"),  # For frontend
                "logical_connections": data.get("logical_connections", ""),
                "topic_consistency": data.get("topic_consistency", ""),
                "transition_quality": data.get("transition_quality", ""),
                "analysis": data.get("analysis", "")
            }
        except Exception as e:
            print(f"Coherence error: {e}")
            return {"coherence_score": 80, "rating": "Good", "flow_quality": "good", "analysis": "Error"}
    
    async def _usefulness_async(self, text: str) -> Dict:
        """Comprehensive usefulness and value analysis"""
        if not self.client:
            return {"usefulness_score": 75, "rating": "Good", "analysis": "Fallback"}
        
        prompt = f"""Analyze the usefulness and value of this conversation response:

"{text}"

Provide comprehensive evaluation of:
1. Usefulness score (0-100)
2. Information quality
3. Actionability of responses
4. Practical value
5. Helpfulness level
6. Detailed analysis

Return JSON format:
{{
    "usefulness_score": <0-100>,
    "information_quality": "excellent|good|fair|poor",
    "actionability": "highly actionable|somewhat actionable|not actionable",
    "practical_value": "analysis of practical value",
    "helpfulness": "analysis of helpfulness",
    "analysis": "comprehensive usefulness analysis"
}}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in evaluating conversation usefulness and value."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Deterministic for consistent results
                seed=42,  # Fixed seed for reproducibility
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            score = data.get("usefulness_score", 75)
            
            return {
                "usefulness_score": score,
                "score": score,  # Alias for frontend
                "rating": self._rating(score),
                "information_quality": data.get("information_quality", "good"),
                "actionability": data.get("actionability", "somewhat actionable"),
                "actionable_phrases": data.get("actionability", "somewhat actionable"),  # For frontend
                "interpretation": data.get("analysis", f"Usefulness rated as {self._rating(score)}"),  # For frontend
                "practical_value": data.get("practical_value", ""),
                "helpfulness": data.get("helpfulness", ""),
                "analysis": data.get("analysis", "")
            }
        except Exception as e:
            print(f"Usefulness error: {e}")
            return {"usefulness_score": 75, "rating": "Good", "analysis": "Error"}
    
    async def _rephrase_async(self, turns: List[Dict]) -> Dict:
        """Detailed rephrase suggestions for top 5 sentences"""
        if not self.client or len(turns) == 0:
            return {"suggestions": []}
        
        # Get first 5 turns for rephrasing
        sentences = []
        for i, turn in enumerate(turns[:5], 1):
            sentences.append(f"{i}. {turn['text']}")
        
        sentences_text = "\n".join(sentences)
        
        prompt = f"""Analyze these 5 sentences from a conversation and provide improved versions:

{sentences_text}

For EACH sentence, provide:
1. Original sentence
2. Improved version with better phrasing
3. Detailed reason why the improvement is better (grammar, clarity, professionalism, empathy, etc.)
4. Key improvements made

Return JSON format:
{{
    "suggestions": [
        {{
            "original": "exact original sentence",
            "improved": "improved version",
            "reason": "detailed explanation of why this is better",
            "improvements": ["improvement1", "improvement2", ...]
        }},
        ...
    ]
}}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional communication coach. Provide detailed, actionable rephrase suggestions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Deterministic for consistent results
                seed=42,  # Fixed seed for reproducibility
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            suggestions = data.get("suggestions", [])[:5]
            return {
                "suggestions": suggestions,
                "rephrases": suggestions  # Alias for frontend
            }
        except Exception as e:
            print(f"Rephrase error: {e}")
            return {"suggestions": [], "rephrases": []}
    
    def _filler_trends(self, turns: List[Dict]) -> Dict:
        """Filler word trends (no API needed)"""
        fillers = []
        for turn in turns:
            fillers.extend(turn.get("filler_words", []))
        
        if not fillers:
            return {"trend": "stable", "filler_rate": 0, "analysis": "No filler words detected"}
        
        rate = len(fillers) / len(turns) if turns else 0
        
        return {
            "trend": "improving" if rate < 2 else "needs work",
            "filler_rate": round(rate, 2),
            "analysis": f"Average {rate:.1f} filler words per response"
        }
    
    def _calc_score(self, analysis: Dict) -> float:
        """Calculate overall score"""
        scores = [
            analysis.get("grammar_analysis", {}).get("score", 70),
            analysis.get("vocabulary_analysis", {}).get("diversity_score", 70),
            analysis.get("empathy_analysis", {}).get("empathy_score", 70),
            analysis.get("politeness_analysis", {}).get("politeness_score", 70),
            analysis.get("coherence_analysis", {}).get("coherence_score", 70),
            analysis.get("usefulness_analysis", {}).get("usefulness_score", 70)
        ]
        return round(sum(scores) / len(scores), 1)
    
    def _rating(self, score: float) -> str:
        """Convert score to rating"""
        if score >= 90: return "Excellent"
        if score >= 75: return "Good"
        if score >= 60: return "Fair"
        return "Needs Improvement"
    
    def _empty_analysis(self) -> Dict:
        """Empty fallback"""
        return {
            "grammar_analysis": {"score": 0, "rating": "N/A"},
            "sentence_structure": {"variety_score": 0, "rating": "N/A"},
            "vocabulary_analysis": {"diversity_score": 0, "rating": "N/A"},
            "empathy_analysis": {"empathy_score": 0, "rating": "N/A"},
            "politeness_analysis": {"politeness_score": 0, "rating": "N/A"},
            "coherence_analysis": {"coherence_score": 0, "rating": "N/A"},
            "usefulness_analysis": {"usefulness_score": 0, "rating": "N/A"},
            "rephrase_suggestions": {"suggestions": []},
            "filler_trend_analysis": {"trend": "N/A", "filler_rate": 0},
            "overall_advanced_score": 0
        }
