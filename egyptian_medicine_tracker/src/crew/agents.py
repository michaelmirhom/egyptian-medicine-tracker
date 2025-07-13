from src.services.medicine_api import medicine_api
from src.services.rxnav_api import rxnav_api
from src.services.local_usage_db import get_local_usage


class PriceAgent:
    @staticmethod
    def run(medicine_name):
        success, products, error = medicine_api.search_and_get_details(medicine_name)
        if success and products:
            return {
                "products": products,
                "found": True
            }
        return {"found": False, "error": error or "Not found"}

class UsageAgent:
    @staticmethod
    def run(medicine_name):
        # First try RxNav
        success, drug_info, error = rxnav_api.get_drug_info(medicine_name)
        if success and drug_info.get("usage_text"):
            return {
                "usage": drug_info["usage_text"],
                "found": True
            }
        # Fallback to local DB
        local_usage = get_local_usage(medicine_name)
        if local_usage:
            return {"usage": local_usage, "found": True}
        return {"found": False, "error": error or "Not found"}

class ChatAgent:
    @staticmethod
    def run(question, price_result, usage_result, history=None, medicine_name=None):
        q = question.lower().strip()
        # Conversation memory for variants
        variants = None
        selected_variant = None
        if history:
            for msg in reversed(history):
                if msg.get('variants'):
                    variants = msg['variants']
                if msg.get('selected_variant'):
                    selected_variant = msg['selected_variant']
                    break
        # Handle greetings and general conversation
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'how are you']
        if any(greeting in q for greeting in greetings):
            return "Hello! I'm your medicine assistant. I can help you with:\n• Medicine usage and indications\n• Medicine prices\n• General medicine information\n\nWhat would you like to know?"
        thanks = ['thank', 'thanks', 'bye', 'goodbye', 'see you']
        if any(thank in q for thank in thanks):
            return "You're welcome! Feel free to ask me anything about medicines anytime. Have a great day!"
        if 'help' in q or 'what can you do' in q:
            return "I'm your medicine assistant! I can help you with:\n\n• **Usage Questions**: 'What is Panadol used for?' or 'What are the indications for Augmentin?'\n• **Price Questions**: 'What's the price of Voltaren?' or 'How much does Concor cost?'\n• **General Info**: 'Tell me about Lipitor' or 'What is Rivo?'\n\nJust ask me anything about medicines!"
        # Handle variant selection by number
        if variants and q.isdigit():
            idx = int(q) - 1
            if 0 <= idx < len(variants):
                selected = variants[idx]
                name = selected.get('name', 'Unknown')
                price = selected.get('price', 'N/A')
                reply = f"The price of {name} is {price} EGP"
                return {'reply': reply, 'selected_variant': selected}
        # Filter variants by medicine_name if provided
        filtered_products = price_result.get('products', [])
        if medicine_name and filtered_products:
            query_lower = medicine_name.strip().lower()
            strict_filtered = [p for p in filtered_products if query_lower in p.get('name', '').lower()]
            # If strict filter left us with no results, fall back to original list
            if strict_filtered:
                filtered_products = strict_filtered

        # Detect if this is primarily a usage question
        is_usage_query = any(kw in q for kw in ['usage', 'used for', 'indication'])

        # If it's a usage question and we have usage information, prioritize returning that.
        if is_usage_query:
            if usage_result.get('found'):
                lines = []
                if medicine_name:
                    lines.append(f"💊 <b>{medicine_name.title()}</b>")
                lines.append(f"🩺 Usage: {usage_result['usage']}")
                # Optionally include price of first match if available uniquely
                if filtered_products:
                    prod = filtered_products[0]
                    price = prod.get('price')
                    if price is not None:
                        lines.append(f"💲 Price: {price} EGP")
                return {'reply': "<br>".join(lines)}
            else:
                return {'reply': "Sorry, usage information is not available for this medicine."}

        # Otherwise, if multiple variants and not a usage-focused query, show variants list.
        if filtered_products and len(filtered_products) > 1:
            variants_text = "\n".join([f"{i+1}. {p.get('name', 'Unknown')} - {p.get('price', 'N/A')} EGP" for i, p in enumerate(filtered_products[:5])])
            return {'reply': f"I found multiple variants for this medicine:\n{variants_text}\n\nPlease reply with the number of the variant you want.", 'variants': filtered_products}
        if filtered_products:
            product = filtered_products[0]
            name = product.get('name', '')
            price = product.get('price', 'N/A')
            reply = f"The price of {name} is {price} EGP"
            return {'reply': reply}
        if not filtered_products:
            return f"No variants found for '{medicine_name}'."
        # Compose answer for medicine information
        med_name = ''
        if filtered_products:
            med_name = filtered_products[0].get('name', '')
        context = ""
        if history:
            for msg in history:
                if msg.get('role') == 'user':
                    context += f"<div style='color:#555'><b>You:</b> {msg['text']}</div>"
                elif msg.get('role') == 'bot':
                    context += f"<div style='color:#222'><b>Bot:</b> {msg['text']}</div>"
        lines = []
        if filtered_products:
            product = filtered_products[0]
            price = product.get('price')
            currency = 'EGP'
            if price:
                lines.append(f"💊 <b>{med_name}</b> price: <b>{price} {currency}</b>")
            if product.get('image'):
                lines.append(f"<img src='{product['image']}' alt='Medicine image' style='max-width:80px;max-height:80px;'>")
        if usage_result.get("found"):
            lines.append(f"🩺 Usage: {usage_result['usage']}")
        if lines:
            return context + "<br>".join(lines)
        else:
            return context + f"Sorry, I couldn't find any information for '{med_name or question}'." 