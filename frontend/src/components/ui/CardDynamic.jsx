"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export const CardDynamic = ({
    processingText = "Processing...",
    title = "Transfer Complete",
    description = "Files have been securely uploaded to the server.",
    buttonText = "View",
    onClick,
    onButtonClick,
    collapsedWidth = "100%",
    collapsedHeight = "6rem",
    expandedWidth = "100%",
    expandedHeight = "20rem",
    backgroundColor = "rgba(16, 12, 36, 0.45)",
    textColor = "#ffffff",
    descriptionColor = "#a0aec0",
    buttonBgColor = "linear-gradient(135deg, var(--color-cyan) 0%, var(--color-purple) 100%)",
    buttonTextColor = "#000000",
    indicatorColor = "rgba(0, 242, 254, 0.2)",
    indicatorSize = "2rem",
    springStiffness = 300,
    springDamping = 30,
    contentDelay = 0.2,
    className = "",
}) => {
    const [expanded, setExpanded] = useState(false);

    return (
        <motion.div
            layout
            onClick={() => {
                setExpanded(!expanded);
                onClick?.();
            }}
            className={cn(
                "cursor-pointer rounded-2xl flex flex-col items-center justify-center overflow-hidden relative border border-slate-800/80 shadow-2xl backdrop-blur-xl transition-all duration-300",
                className
            )}
            style={{
                width: expanded ? expandedWidth : collapsedWidth,
                height: expanded ? expandedHeight : collapsedHeight,
                backgroundColor,
            }}
            transition={{ type: "spring", stiffness: springStiffness, damping: springDamping }}
        >
            <motion.div layout className="absolute top-6 flex items-center gap-4">
                <div
                    className="rounded-full animate-pulse flex items-center justify-center"
                    style={{
                        width: indicatorSize,
                        height: indicatorSize,
                        backgroundColor: indicatorColor,
                    }}
                >
                    <div className="w-2 h-2 rounded-full bg-cyan-400" />
                </div>
                {!expanded && (
                    <motion.span
                        layoutId="text"
                        className="font-medium tracking-wide"
                        style={{ color: textColor }}
                    >
                        {processingText}
                    </motion.span>
                )}
            </motion.div>

            {expanded && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: contentDelay }}
                    className="mt-14 text-center px-6 w-full flex flex-col items-center"
                >
                    <h3
                        className="text-lg font-bold"
                        style={{ color: textColor }}
                    >
                        {title}
                    </h3>
                    <p
                        className="text-sm mt-2 leading-relaxed"
                        style={{ color: descriptionColor }}
                    >
                        {description}
                    </p>
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onButtonClick?.();
                        }}
                        className="mt-6 w-full py-2.5 rounded-xl font-bold uppercase tracking-wider text-[11px] hover:scale-[1.02] active:scale-[0.98] transition-transform"
                        style={{
                            background: buttonBgColor,
                            color: buttonTextColor,
                            border: "none",
                        }}
                    >
                        {buttonText}
                    </button>
                </motion.div>
            )}
        </motion.div>
    );
};

export default CardDynamic;
