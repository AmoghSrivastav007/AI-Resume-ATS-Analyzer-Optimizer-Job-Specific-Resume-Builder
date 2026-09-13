import { AuthForm } from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <div className="flex flex-1 items-center justify-center bg-zinc-50 px-4 py-16">
      <AuthForm mode="login" />
    </div>
  );
}
