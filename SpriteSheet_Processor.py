import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os

class SpriteProcessorApp:
    def __init__(self, master):
        self.master = master
        master.title("精灵图紧凑拼接工具")
        master.geometry("450x400") # 调整窗口大小

        self.image_path = None
        self.original_image = None
        self.processed_image = None
        self.grid_rows = tk.IntVar(value=4) # 默认4行
        self.grid_cols = tk.IntVar(value=4) # 默认4列

        # --- UI Elements ---
        # Frame for file operations
        file_frame = ttk.Frame(master, padding="10")
        file_frame.pack(fill=tk.X)

        self.load_button = ttk.Button(file_frame, text="加载精灵图", command=self.load_image)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.file_label = ttk.Label(file_frame, text="未加载图片", relief=tk.SUNKEN, padding=5)
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Frame for grid selection
        grid_frame = ttk.LabelFrame(master, text="选择网格尺寸", padding="10")
        grid_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Radiobutton(grid_frame, text="4x4", variable=self.grid_rows, value=4, command=lambda: self.grid_cols.set(4)).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(grid_frame, text="3x4 (3列4行)", variable=self.grid_rows, value=4, command=lambda: self.grid_cols.set(3)).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(grid_frame, text="4x3 (4列3行)", variable=self.grid_rows, value=3, command=lambda: self.grid_cols.set(4)).pack(side=tk.LEFT, padx=10)


        # Frame for actions
        action_frame = ttk.Frame(master, padding="10")
        action_frame.pack(fill=tk.X)

        self.process_button = ttk.Button(action_frame, text="处理图片", command=self.process_image, state=tk.DISABLED)
        self.process_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(action_frame, text="保存结果", command=self.save_image, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        # Frame for preview (optional, basic)
        preview_frame = ttk.LabelFrame(master, text="预览 (处理后)", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.preview_label = ttk.Label(preview_frame, text="处理后可预览")
        self.preview_label.pack(pady=10)
        self.preview_image_tk = None # To hold the PhotoImage reference

        # Status bar
        self.status_label = ttk.Label(master, text="准备就绪", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="选择精灵图文件",
            filetypes=[("PNG 图片", "*.png"), ("所有文件", "*.*")]
        )
        if file_path:
            self.image_path = file_path
            try:
                self.original_image = Image.open(self.image_path).convert("RGBA")
                self.file_label.config(text=os.path.basename(file_path))
                self.status_label.config(text=f"已加载: {os.path.basename(file_path)}")
                self.process_button.config(state=tk.NORMAL)
                self.save_button.config(state=tk.DISABLED) # Disable save until processed
                self.processed_image = None # Reset processed image
                self.preview_label.config(image='', text='图片已加载，请处理') # Clear preview
                self.preview_image_tk = None
            except Exception as e:
                messagebox.showerror("加载错误", f"无法加载图片: {e}")
                self.image_path = None
                self.original_image = None
                self.file_label.config(text="加载失败")
                self.status_label.config(text="加载图片失败")
                self.process_button.config(state=tk.DISABLED)

    def process_image(self):
        if not self.original_image:
            messagebox.showwarning("未加载图片", "请先加载一张图片。")
            return

        rows = self.grid_rows.get()
        cols = self.grid_cols.get()

        self.status_label.config(text=f"正在处理 {cols}x{rows} 网格...")
        self.master.update_idletasks() # Update UI to show status

        try:
            img_w, img_h = self.original_image.size
            # Estimate cell size (including potential padding)
            cell_w_est = img_w // cols
            cell_h_est = img_h // rows

            tiles_data = []
            max_tile_w = 0
            max_tile_h = 0

            for r in range(rows):
                for c in range(cols):
                    # Define the estimated box for the current tile
                    box_est = (c * cell_w_est, r * cell_h_est, (c + 1) * cell_w_est, (r + 1) * cell_h_est)
                    # Crop the estimated area
                    tile_est = self.original_image.crop(box_est)
                    # Find the bounding box of non-transparent pixels in this estimated tile
                    bbox = tile_est.getbbox()
                    if bbox:
                        # Crop to the actual content using the bounding box
                        actual_tile = tile_est.crop(bbox)
                        tile_w, tile_h = actual_tile.size
                        tiles_data.append(actual_tile)
                        max_tile_w = max(max_tile_w, tile_w)
                        max_tile_h = max(max_tile_h, tile_h)
                    else:
                        # Handle empty tiles if necessary, maybe append None or a placeholder
                        # For simplicity, we assume all grid cells have content
                        # If a tile is completely transparent, getbbox returns None.
                        # We might need a strategy here, e.g., skip or add an empty space of max size.
                        # Let's append an empty image of size 0 for now, max size logic will handle it.
                        tiles_data.append(Image.new("RGBA", (0,0), (0,0,0,0)))


            if max_tile_w == 0 or max_tile_h == 0:
                 messagebox.showerror("处理错误", "未能检测到任何有效的瓦片内容。")
                 self.status_label.config(text="处理失败：未检测到瓦片。")
                 return

            # Create the new image canvas (transparent)
            new_img_w = max_tile_w * cols
            new_img_h = max_tile_h * rows
            self.processed_image = Image.new('RGBA', (new_img_w, new_img_h), (0, 0, 0, 0))

            # Paste tiles onto the new canvas
            tile_index = 0
            for r in range(rows):
                for c in range(cols):
                    if tile_index < len(tiles_data):
                        tile = tiles_data[tile_index]
                        if tile.size[0] > 0: # Only paste if tile has content
                            # Calculate paste position (top-left corner of the cell)
                            paste_x = c * max_tile_w
                            paste_y = r * max_tile_h
                            # Paste using the tile itself as the mask for transparency
                            self.processed_image.paste(tile, (paste_x, paste_y), tile)
                        tile_index += 1

            self.status_label.config(text="处理完成！可以保存或预览。")
            self.save_button.config(state=tk.NORMAL)
            self.show_preview() # Show preview after processing

        except Exception as e:
            messagebox.showerror("处理错误", f"处理图片时发生错误: {e}")
            self.status_label.config(text=f"处理失败: {e}")
            self.processed_image = None
            self.save_button.config(state=tk.DISABLED)
            self.preview_label.config(image='', text='处理失败')
            self.preview_image_tk = None


    def show_preview(self):
        if not self.processed_image:
            return

        # Resize for preview if too large
        max_preview_size = 200
        img = self.processed_image.copy()
        img.thumbnail((max_preview_size, max_preview_size))

        self.preview_image_tk = ImageTk.PhotoImage(img)
        self.preview_label.config(image=self.preview_image_tk, text='') # Display image, clear text


    def save_image(self):
        if not self.processed_image:
            messagebox.showwarning("没有结果", "请先成功处理一张图片。")
            return

        save_path = filedialog.asksaveasfilename(
            title="保存处理后的图片",
            defaultextension=".png",
            filetypes=[("PNG 图片", "*.png")],
            initialfile=f"{os.path.splitext(os.path.basename(self.image_path))[0]}_processed.png"
        )

        if save_path:
            try:
                self.processed_image.save(save_path, "PNG")
                self.status_label.config(text=f"图片已保存到: {save_path}")
                messagebox.showinfo("保存成功", f"图片已成功保存到:\n{save_path}")
            except Exception as e:
                messagebox.showerror("保存错误", f"无法保存图片: {e}")
                self.status_label.config(text="保存图片失败")

if __name__ == "__main__":
    root = tk.Tk()
    app = SpriteProcessorApp(root)
    root.mainloop()