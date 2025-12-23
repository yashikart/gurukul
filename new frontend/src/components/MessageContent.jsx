import React from 'react';

/**
 * Component to render message content with clickable links
 * Converts markdown-style links [text](url) to clickable <a> tags
 */
const MessageContent = ({ content }) => {
  // Function to convert markdown links to React elements
  const parseContent = (text) => {
    if (!text) return null;

    // Regex to match markdown links: [text](url)
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = linkRegex.exec(text)) !== null) {
      // Add text before the link
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.substring(lastIndex, match.index)
        });
      }

      // Add the link
      parts.push({
        type: 'link',
        text: match[1],
        url: match[2]
      });

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text after the last link
    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.substring(lastIndex)
      });
    }

    // If no links found, return original text
    if (parts.length === 0) {
      return text;
    }

    // Render parts as React elements
    return parts.map((part, index) => {
      if (part.type === 'link') {
        return (
          <a
            key={index}
            href={part.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 underline break-all"
            style={{
              wordBreak: 'break-all',
              overflowWrap: 'break-word'
            }}
          >
            {part.text}
          </a>
        );
      }
      return <span key={index}>{part.content}</span>;
    });
  };

  const parsedContent = parseContent(content);

  return (
    <>
      {parsedContent || content}
    </>
  );
};

export default MessageContent;

