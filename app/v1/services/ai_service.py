import google.generativeai as genai
from app.core.config import settings
from flask import render_template_string
import json
import re
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def get_suggestions(self, category: str, user_prompt: str):
        # The Jinja2 System Instruction Template
        system_template = """
You are an expert resource recommendation engine with deep knowledge of popular, high-quality content.

Category: {{ category }}
User Request: {{ prompt }}

YOUR MISSION:
Recommend exactly 3 REAL, POPULAR, and WIDELY-KNOWN resources that match the user's request.

LINK GENERATION RULES (CRITICAL):
1. **For Movies/TV Shows**: 
   - Use IMDb format: https://www.imdb.com/title/tt[ID]/ (only if you know the exact ID)
   - Otherwise use: https://www.imdb.com/find/?q=[Movie+Name]
   - Example: https://www.imdb.com/find/?q=Inception

2. **For YouTube Videos/Tutorials**:
   - ONLY recommend channels you're certain exist: FreeCodeCamp, Traversy Media, Programming with Mosh, Corey Schafer, Tech With Tim, Fireship, The Net Ninja
   - Use search format: https://www.youtube.com/results?search_query=[topic]
   - Example: https://www.youtube.com/results?search_query=python+tutorial+for+beginners

3. **For Articles/Blogs**:
   - Use well-known platforms: Medium, Dev.to, freeCodeCamp News, CSS-Tricks, Smashing Magazine
   - Format: https://[platform].com/search?q=[topic]
   - Example: https://medium.com/search?q=react+hooks+tutorial

4. **For Documentation**:
   - Use official docs URLs: 
     * Python: https://docs.python.org/3/
     * JavaScript: https://developer.mozilla.org/en-US/docs/Web/JavaScript
     * React: https://react.dev/
   - If unsure, use: https://www.google.com/search?q=[technology]+official+documentation

5. **For GitHub Projects**:
   - ONLY recommend extremely popular projects you're certain exist
   - Format: https://github.com/[username]/[repo]
   - If unsure: https://github.com/search?q=[topic]

6. **For Books**:
   - Use Goodreads: https://www.goodreads.com/search?q=[book+title]
   - Example: https://www.goodreads.com/search?q=clean+code

7. **For Podcasts**:
   - Use Spotify search: https://open.spotify.com/search/[podcast+name]
   - Example: https://open.spotify.com/search/syntax%20fm

8. **For General Resources**:
   - Use Google search format: https://www.google.com/search?q=[query]
   - Replace spaces with + signs
   - Example: https://www.google.com/search?q=best+thriller+movies+2023

QUALITY STANDARDS:
- Recommend ONLY well-known, popular resources (millions of views, thousands of stars, widely referenced)
- For technical content: Prioritize official documentation, major tutorial channels, and established educators
- For entertainment: Prioritize critically acclaimed, award-winning, or cult classic content
- Include accurate ratings from reputable sources (IMDb, Rotten Tomatoes, GitHub stars, etc.)

OUTPUT FORMAT (ABSOLUTELY CRITICAL):
You MUST return ONLY a valid JSON array. Follow these rules EXACTLY:

1. Start your response with [ and end with ]
2. NO text before the [
3. NO text after the ]
4. NO markdown code blocks (no ``` at all)
5. NO explanations or comments
6. Use double quotes " for all strings (not single quotes ')
7. Escape any quotes inside strings with \"

The ONLY thing in your response should be:

[
  {
    "name": "Specific Resource Title",
    "description": "Concise description (max 120 words)",
    "rating": "8.5/10 IMDb",
    "link": "https://valid-url.com"
  },
  {
    "name": "Second Resource",
    "description": "Description here",
    "rating": "Rating here",
    "link": "https://another-url.com"
  },
  {
    "name": "Third Resource",
    "description": "Description here",
    "rating": "Rating here",
    "link": "https://third-url.com"
  }
]

EXAMPLES OF CORRECT FORMAT:

[
  {
    "name": "Python Tutorial - Full Course for Beginners by freeCodeCamp",
    "description": "Comprehensive 4.5-hour Python tutorial covering fundamentals, data structures, and practical projects. Perfect for complete beginners with clear explanations and hands-on examples.",
    "rating": "4.8/5 (2M+ views)",
    "link": "https://www.youtube.com/results?search_query=python+tutorial+freecodecamp"
  },
  {
    "name": "Official Python Documentation",
    "description": "The authoritative Python tutorial from the official Python Software Foundation. Covers language basics, standard library, and best practices with detailed examples.",
    "rating": "Official Documentation",
    "link": "https://docs.python.org/3/tutorial/"
  },
  {
    "name": "Automate the Boring Stuff with Python",
    "description": "Practical Python programming book by Al Sweigart focusing on real-world automation tasks. Free online version available with excellent beginner-friendly explanations.",
    "rating": "4.6/5 (50K+ ratings)",
    "link": "https://automatetheboringstuff.com/"
  }
]

WRONG RESPONSES (DO NOT DO THIS):
❌ Here are some recommendations: [...]
❌ ```json [...]```
❌ I found these resources: [...]
❌ [{"name": 'Title'}]  (single quotes)

REMEMBER: Your ENTIRE response must be ONLY the JSON array. Nothing else.
"""
        
        # Render the instruction with current data
        full_prompt = render_template_string(
            system_template, 
            category=category, 
            prompt=user_prompt
        )
        
        try:
            # Generate content with stricter configuration
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,  # Lower temperature for more consistent output
                    top_p=0.9,
                    max_output_tokens=2048,
                )
            )
            
            # Check if response exists
            if not response or not response.text:
                logger.error("Empty response from Gemini API")
                return json.dumps([])
            
            # Get the raw text
            raw_text = response.text.strip()
            logger.info(f"Raw AI response (first 200 chars): {raw_text[:200]}")
            
            # Clean the response
            cleaned_text = self._clean_response(raw_text)
            
            # Validate and parse JSON
            validated_data = self._validate_json(cleaned_text, category, user_prompt)
            
            # Return as JSON string
            return json.dumps(validated_data)
            
        except Exception as e:
            logger.error(f"AI Service Error: {str(e)}")
            return json.dumps([])
    
    def _clean_response(self, text: str) -> str:
        """Clean the AI response to extract valid JSON"""
        
        # Remove any text before the first [
        if '[' in text:
            text = text[text.index('['):]
        
        # Remove any text after the last ]
        if ']' in text:
            text = text[:text.rindex(']') + 1]
        
        # Remove markdown code blocks if present
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
        
        # Remove any leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _validate_json(self, text: str, category: str, user_prompt: str) -> list:
        """Validate and parse JSON, return valid list or fallback"""
        
        try:
            # Parse JSON
            data = json.loads(text)
            
            # Check if it's a list
            if not isinstance(data, list):
                logger.error("Response is not a list")
                return self._get_fallback(category, user_prompt)
            
            # Validate each item
            valid_items = []
            required_fields = ['name', 'description', 'rating', 'link']
            
            for item in data[:3]:  # Take only first 3
                if isinstance(item, dict) and all(field in item for field in required_fields):
                    # Ensure link is a valid URL
                    if not item['link'].startswith('http'):
                        search_query = item['name'].replace(' ', '+')
                        item['link'] = f"https://www.google.com/search?q={search_query}"
                    
                    # Ensure all values are strings
                    item['name'] = str(item['name'])
                    item['description'] = str(item['description'])
                    item['rating'] = str(item['rating'])
                    item['link'] = str(item['link'])
                    
                    valid_items.append(item)
                else:
                    logger.warning(f"Invalid item structure: {item}")
            
            # If we have at least one valid item, return them
            if valid_items:
                return valid_items
            else:
                logger.error("No valid items found in response")
                return self._get_fallback(category, user_prompt)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Attempted to parse: {text[:500]}")
            return self._get_fallback(category, user_prompt)
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return self._get_fallback(category, user_prompt)
    
    def _get_fallback(self, category: str, user_prompt: str) -> list:
        """Generate fallback recommendations when AI fails"""
        search_query = user_prompt.replace(' ', '+')
        category_query = category.replace(' ', '+')
        
        return [
            {
                "name": f"Search: {user_prompt}",
                "description": f"We couldn't generate specific recommendations for '{user_prompt}'. Click this link to search for relevant {category} resources on Google.",
                "rating": "N/A",
                "link": f"https://www.google.com/search?q={search_query}+{category_query}"
            },
            {
                "name": f"YouTube: {category} for {user_prompt}",
                "description": f"Find video tutorials and content related to '{user_prompt}' in the {category} category on YouTube.",
                "rating": "N/A",
                "link": f"https://www.youtube.com/results?search_query={search_query}+{category_query}"
            },
            {
                "name": f"Explore {category} Resources",
                "description": f"Browse popular {category} resources and discover content similar to what you're looking for.",
                "rating": "N/A",
                "link": f"https://www.google.com/search?q=best+{category_query}+resources"
            }
        ]

# Instantiate the service
ai_engine = AIService()

