export type Language = 'nl' | 'en';
export interface Person {
    fullName: string,
    url: string
}

export interface Department {
    slug: string,
    descriptions: DepartmentDescription[]
}

export interface DepartmentDescription {
    name: string,
    text: string,
    language: Language
}

export interface ExchangeSessionDescription {
    date: string
    language: Language
    location: string,
    title: string,
    subtitle: string,
    intro: string,
    program: string
}

export interface ExchangeSession {
    title: string;
    sortTitle: string;
    department: Department,
    descriptions: ExchangeSessionDescription[],
    participantsMax: number,
    participantsMin: number,
    pk: number,
    sessionCount: number,
    organizers: Person[],
    full: boolean
}
