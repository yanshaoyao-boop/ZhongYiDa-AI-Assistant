export interface ImageAsset {
    buffer: ArrayBuffer;
    extension: 'jpeg' | 'png' | 'gif';
    width?: number;
    height?: number;
}

export interface OrderRow {
    _source: string;
    // Dynamic keys from Excel columns
    [key: string]: any;
}

export interface RowWithImages extends OrderRow {
    _images?: ImageAsset[];
}

export interface ColumnMapping {
    index: number;
    name: string;
}

export interface TemplateConfig {
    groupBy: string;
    sumBy: string;
    declareType: string;
}

export type WarehouseMap = Record<string, (string | number | null)[]>;
