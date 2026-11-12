
text = "Spasova, S., Ghailani, D., Sabato, S., Coster, S., Fronteddu, B., & Vanhercke, B. (2021).  Non-standard Workers and the Self employed in the EU: Social Protection During  the Covid-19 Pandemic. ETUI Research Paper – Report 2021.02.  Statistics Netherlands (CBS) (2024), ‘Fewer workers in flexible employment and more on  permanent contracts’.  Swiss Confederation Central Compensation Office (CCO) (2024), Agreement on the Free  Movement of Persons - EU [Online]: https://www.zas.admin.ch/zas/en/home/bases- legales-et-coordination-internationale/coordination_internationale_securite_socia  le/accord_libre_circulation_ue.html  Teney, C. (2021), Immigration of highly skilled European professionals to Germany: intra- EU brain gain or brain circulation?, Innovation: The European Journal of Social  Science Research, 34(1), 69-92.  United Nations (2020). COVID-19 and social protection in Europe and Central Asia: A  moment of opportunity to expand and strengthen social protection mechanisms to  safeguard health, well-being and livelihoods, leaving no one behind.   van Kessel, R., Wong, B. L. H., Rubinić, I., O’Nuallain, E., & Czabanowska, K. (2022). Is  Europe prepared to go digital? making the case for developing digital capacity: An  exploratory analysis of Eurostat survey data. PLOS Digital Health, 1(2), e0000013. "
OVERLAP = 40
CHUNK_SIZE = 100


def chunk_text():
    start = 0
    index = 0
    chunks = []
    end = len(text)
    while start < len(text):
        end = min(start+CHUNK_SIZE, len(text))
        text_item = text[start:end]
        index +=1
        chunks.append({index:text_item})

        if end == len(text):
            break

        start = end - OVERLAP
    return chunks


print(chunk_text())