import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { CanvasAspect } from '../../models';

@Component({
  selector: 'app-canvas-aspect-card-item',
  templateUrl: './canvas-aspect-card-item.component.html',
  styleUrls: ['./canvas-aspect-card-item.component.css']
})
export class CanvasAspectCardItemComponent implements OnInit {
  @Input() canvasAspect: CanvasAspect;
  @Output() select = new EventEmitter<string>();

  constructor() {}

  ngOnInit() {}
}
