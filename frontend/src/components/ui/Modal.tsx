"use client";

import { useEffect, useRef, type MouseEvent, type ReactNode } from "react";

/** Built on native <dialog> for free focus-trap, ESC-to-close, and a
 * backdrop -- per modals.md's accessibility requirement without hand-rolling
 * a focus trap. */
export function Modal({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  function handleBackdropClick(event: MouseEvent<HTMLDialogElement>) {
    if (event.target === dialogRef.current) onClose();
  }

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      onCancel={onClose}
      onClick={handleBackdropClick}
      className="m-auto rounded-lg border-none bg-neutral-primary p-0 shadow-xl backdrop:bg-dark/50 backdrop:backdrop-blur-sm"
    >
      <div className="w-[min(90vw,28rem)]">
        <div className="flex items-center justify-between rounded-t-lg border-b border-border-default p-5">
          <h2 className="text-lg font-semibold text-heading">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-full p-1.5 text-body transition-colors hover:bg-neutral-secondary-medium hover:text-heading"
          >
            ✕
          </button>
        </div>
        <div className="space-y-4 p-5">{children}</div>
      </div>
    </dialog>
  );
}
