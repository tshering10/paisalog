import { getCategories } from "@/lib/categories-api";
import { CategoryManager } from "@/components/categories/category-manager";

export default async function CategoriesPage() {
  const categories = await getCategories();

  return (
    <div>
      <p className="text-sm font-semibold text-primary">Organize your money</p>
      <h1 className="mt-1 font-heading text-3xl font-bold text-text">Categories</h1>
      <p className="mt-2 text-sm text-text-muted">Use categories to make your spending easier to understand.</p>
      <div className="mt-8">
        <CategoryManager categories={categories} />
      </div>
    </div>
  );
}
