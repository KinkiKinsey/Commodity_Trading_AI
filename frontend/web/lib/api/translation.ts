import { NEWS_TRANSLATION_ENDPOINT } from "@/lib/config/env";

export type TranslationRequestItem = {
  id: string;
  text: string;
};

export type TranslationResponse = {
  translations: Record<string, string>;
};

const DEFAULT_RESPONSE: TranslationResponse = { translations: {} };

export async function requestTranslations(
  items: TranslationRequestItem[],
  targetLocale: string
): Promise<Record<string, string>> {
  if (!items.length) {
    return {};
  }

  try {
    const response = await fetch(NEWS_TRANSLATION_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        target_locale: targetLocale,
        items
      })
    });

    if (!response.ok) {
      throw new Error(`Translation request failed (${response.status})`);
    }

    const payload = (await response.json()) as TranslationResponse;
    return payload.translations ?? {};
  } catch (error) {
    console.error("Failed to fetch translations", error);
    return {};
  }
}
