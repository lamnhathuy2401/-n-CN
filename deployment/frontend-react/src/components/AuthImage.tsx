import { useEffect, useState } from "react";
import { imageUrl } from "../api";
import { useAuth } from "../auth";

export function AuthImage({
  submissionId,
  imageId,
  alt,
  className,
}: {
  submissionId: number;
  imageId: number;
  alt: string;
  className?: string;
}) {
  const { token } = useAuth();
  const [src, setSrc] = useState<string>("");

  useEffect(() => {
    let objectUrl = "";
    let cancelled = false;
    async function load() {
      if (!token) return;
      const res = await fetch(imageUrl(submissionId, imageId), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok || cancelled) return;
      const blob = await res.blob();
      objectUrl = URL.createObjectURL(blob);
      if (!cancelled) setSrc(objectUrl);
    }
    load();
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [token, submissionId, imageId]);

  return <img className={className} src={src} alt={alt} />;
}
