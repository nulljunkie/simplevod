package utils

import (
	"regexp"
	"strings"
	"unicode"
)

func SanitizeLabel(input string) string {
	reg := regexp.MustCompile(`[^a-zA-Z0-9-_\.]+`)
	sanitized := reg.ReplaceAllString(input, "-")

	sanitized = strings.TrimFunc(sanitized, func(r rune) bool {
		return !unicode.IsLetter(r) && !unicode.IsNumber(r)
	})

	if len(sanitized) > 63 {
		sanitized = sanitized[:63]
		sanitized = strings.TrimRightFunc(sanitized, func(r rune) bool {
			return !unicode.IsLetter(r) && !unicode.IsNumber(r)
		})
	}
	if sanitized == "" {
		return "default-label"
	}

	return strings.ToLower(sanitized)
}
