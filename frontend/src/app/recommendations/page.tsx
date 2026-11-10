import { redirect } from "next/navigation";

/**
 * Recommendations are rendered by the Scheme Discovery experience, which
 * already sources them from the backend recommendation engine. Keep the
 * historical route working instead of returning a 404.
 */
export default function RecommendationsPage() {
  redirect("/schemes");
}
