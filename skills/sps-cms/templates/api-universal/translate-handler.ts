/**
 * SPS-CMS Gemini Flash Universal Multi-Language Auto-Translator
 * Uses Google Gemini 2.0 / 1.5 Flash via lightweight native fetch (Zero-Dependency)
 */

export interface TranslationRequest {
  text: string;
  sourceLang?: string; // e.g. "en"
  targetLangs: string[]; // e.g. ["bn", "ar"]
}

export async function translateWithGeminiFlash(
  req: TranslationRequest,
  apiKey: string = process.env.GEMINI_API_KEY || ''
): Promise<Record<string, string>> {
  if (!apiKey) {
    throw new Error('GEMINI_API_KEY is not configured in .env or settings');
  }

  const source = req.sourceLang || 'en';
  const targets = req.targetLangs.join(', ');

  const prompt = `
You are a professional multilingual translator for a high-end luxury CMS.
Translate the following web content from ${source} into the following target languages: ${targets}.
Maintain tone, context, and formatting.

Source Content:
"${req.text}"

Return ONLY a valid JSON object mapping each target language code to its translated string.
Example format:
{
  "bn": "বাংলা অনুবাদ",
  "ar": "الترجمة العربية"
}
`;

  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: {
        responseMimeType: 'application/json',
        temperature: 0.2
      }
    })
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Gemini API error (${response.status}): ${errText}`);
  }

  const data = await response.json();
  const rawText = data.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!rawText) return {};

  try {
    return JSON.parse(rawText);
  } catch {
    return {};
  }
}
