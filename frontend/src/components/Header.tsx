import Link from "next/link";

export default function Header() {
  return (
    <header className="border-b border-line bg-white">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        <Link href="/" className="hover:text-primary">
          공고그대로
        </Link>
        <nav className="text-sm text-sub">
          <Link href="/" className="hover:text-primary">
            새로비교하기
          </Link>
        </nav>
      </div>
    </header>
  );
}
